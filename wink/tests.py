from django.test import TestCase
from .models import Task, SubTask, Team, User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class CreateTaskAPITestCase(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(name='단비')
        self.other_team = Team.objects.create(name='다래')
        self.user = User.objects.create_user(email='testuser', password='testpassword', team=self.team)
        self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_create_task_with_subtasks(self):
        data = {
            'task': {
                'team_id': self.team.id,
                'title': 'Task Title',
                'content': 'Task Content',
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.post('/v1/api/tasks', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 업무(Task)가 생성되었는지 확인
        self.assertTrue('title' in response.data)

        # 업무(Task) 작성자 확인
        self.assertEqual(response.data['create_user'], self.user.id)

        # 업무(Task) 완료여부 확인
        self.assertEqual(response.data['is_complete'], False)

        # 업무의(Task) 완료일자 컬럼이 null이어야 함
        self.assertEqual(response.data['completed_date'], None)

        # 하위 업무(SubTask) 2건 생성되었는지 확인
        self.assertEqual(len(response.data['subtasks']), 2)

        # 완료된 하위 업무(SubTask) 0개여야 함
        completed_subtasks_count = sum(1 for subtask in response.data['subtasks'] if subtask['is_complete'])
        self.assertEqual(completed_subtasks_count, 0)

        # 하위 업무(SubTask) 완료일자 컬럼이 null이어야 함
        completed_date_null_count = sum(1 for subtask in response.data['subtasks'] if not subtask['completed_date'])
        self.assertEqual(completed_date_null_count, 2)

    def test_create_task_with_blank_title(self):
        data = {
            'task': {
                'team_id': self.team.id,
                'title': '',  # 빈 문자열
                'content': 'Task Content',
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.post('/v1/api/tasks', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_task_with_blank_content(self):
        data = {
            'task': {
                'team_id': self.team.id,
                'title': 'Valid Task Title',
                'content': '',  # 빈 문자열
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.post('/v1/api/tasks', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_with_invalid_team(self):
        data = {
            'task': {
                'team_id': 9999, # 존재하지 않는 팀 ID
                'title': 'Valid Task Title',
                'content': 'Task Content',
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.post('/v1/api/tasks', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_with_none_team_field(self):
        data = {
            'task': {
                # team_id 필드 누락
                'title': 'Valid Task Title',
                'content': 'Valid Task Content',
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.post('/v1/api/tasks', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_with_none_subtasks_field(self):
        data = {
            'task': {
                'team_id': 1,
                'title': 'Valid Task Title',
                'content': 'Valid Task Content',
                # subtasks 필드 누락
            },
        }
        response = self.client.post('/v1/api/tasks', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_with_unmodifiable_field(self):
        data = {
            'task': {
                'team_id': self.team.id,
                'title': 'Task Title',
                'content': 'Task Content',
                'is_complete': True, # 사용자가 입력 불가한 항목
                'subtasks': [
                    {
                        'team_id': self.team.id,
                        'is_complete': True, # 사용자가 입력 불가한 항목
                    },
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.post('/v1/api/tasks', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 업무(Task) 완료여부 확인
        self.assertEqual(response.data['is_complete'], False)

        # 업무의(Task) 완료일자 컬럼이 null이어야 함
        self.assertEqual(response.data['completed_date'], None)

        # 완료된 하위 업무(SubTask) 0개여야 함
        completed_subtasks_count = sum(1 for subtask in response.data['subtasks'] if subtask['is_complete'])
        self.assertEqual(completed_subtasks_count, 0)

        # 하위 업무(SubTask) 완료일자 컬럼이 null이어야 함
        completed_date_null_count = sum(1 for subtask in response.data['subtasks'] if not subtask['completed_date'])
        self.assertEqual(completed_date_null_count, 2)

class SelectTaskAPITestCase(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(name='단비')
        self.other_team = Team.objects.create(name='다래')
        self.user = User.objects.create_user(email='testuser', password='testpassword', team=self.team)
        self.user.save()
        self.client.force_authenticate(user=self.user)
    
    def test_select_task_list(self):
        # 내 팀 업무 생성
        my_team_task1 = Task.objects.create(team=self.team, title='My Team Task 1', content='Task Content')
        my_team_task2 = Task.objects.create(team=self.team, title='My Team Task 2', content='Task Content')
        
        # 서브업무 생성
        subtask1 = SubTask.objects.create(team=self.team, task=my_team_task1)
        subtask2 = SubTask.objects.create(team=self.other_team, task=my_team_task2)

        my_team_task1.subtasks.add(subtask1)
        my_team_task2.subtasks.add(subtask2)

        # 다른 팀 업무 생성
        other_team_task1 = Task.objects.create(team=self.other_team, title='Other Team Task 1', content='Task Content')
        other_team_task2 = Task.objects.create(team=self.other_team, title='Other Team Task 2', content='Task Content')

        # 서브업무 생성
        subtask1 = SubTask.objects.create(team=self.team, task=other_team_task1)
        subtask2 = SubTask.objects.create(team=self.other_team, task=other_team_task1)
        subtask3 = SubTask.objects.create(team=self.other_team, task=other_team_task2)
        subtask4 = SubTask.objects.create(team=self.other_team, task=other_team_task2)

        other_team_task1.subtasks.add(subtask1, subtask2)
        other_team_task2.subtasks.add(subtask3, subtask4)

        response = self.client.get('/v1/api/tasks')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 내 팀 업무 2 + 다른 팀 업무(서무 내 업무) 1
        self.assertEqual(len(response.data), 3)

        # 내 업무에 보여야할 목록
        task_titles = [task['title'] for task in response.data]
        self.assertIn('My Team Task 1', task_titles)
        self.assertIn('My Team Task 2', task_titles)
        self.assertIn('Other Team Task 1', task_titles)

        # 다른 팀 업무는 조회되면 안됨
        self.assertNotIn('Other Team Task 2', task_titles)

        # 1,2,3 각각 서브업무가 1,1,2 개 조회되어야함
        self.assertEqual(len(response.data[0]['subtasks']), 2)
        self.assertEqual(len(response.data[1]['subtasks']), 1)
        self.assertEqual(len(response.data[2]['subtasks']), 1)

        # 업무 순서가 최근 것부터 나와야함
        self.assertEqual(response.data[0]['title'], 'Other Team Task 1')
        self.assertEqual(response.data[1]['title'], 'My Team Task 2')
        self.assertEqual(response.data[2]['title'], 'My Team Task 1')

class UpdateTaskAPITestCase(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(name='단비')
        self.other_team = Team.objects.create(name='다래')
        self.user = User.objects.create_user(email='testuser', password='testpassword', team=self.team)
        self.user.save()
        self.other_user = User.objects.create_user(email='testuser2', password='testpassword2', team=self.team)
        self.other_user.save()
        self.client.force_authenticate(user=self.user)

    # 기존 subtasks의 팀을 바꾸는 파라미터, 
    def test_patch_task_with_subtasks(self):
        # 내 팀 업무 생성
        my_team_task1 = Task.objects.create(create_user=self.user, team=self.team, title='My Team Task 1', content='Task Content')
        # 서브업무 생성
        subtask1 = SubTask.objects.create(team=self.team, task=my_team_task1, is_complete=True) # 수정 불가한 서브 업무
        subtask2 = SubTask.objects.create(team=self.team, task=my_team_task1, is_complete=False) # 수정할 서브 업무
        subtask3 = SubTask.objects.create(team=self.other_team, task=my_team_task1, is_complete=True) # 삭제 불가한 서브 업무
        subtask4 = SubTask.objects.create(team=self.other_team, task=my_team_task1, is_complete=False) # 삭제될 서브 업무
        my_team_task1.subtasks.add(subtask1, subtask2, subtask3, subtask4)

        data = {
            'task': {
                'team_id': self.other_team.id,
                'title': 'Patch Valid Task Title',
                'content': 'Patch Task Content',
                'subtasks': [
                    {
                        'id': subtask1.id,           # 수정 불가 서브업무
                        'team_id': self.other_team.id   
                    },
                    {
                        'id': subtask2.id,           # 수정 서브업무
                        'team_id': self.other_team.id   
                    }
                    ,
                    {'team_id': self.other_team.id}, # 신규 서브업무
                ]
            },
        }
        response = self.client.patch(f'/v1/api/tasks/{my_team_task1.id}', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 업무 team_id 변경 여부 확인
        self.assertEqual(response.data['team'], self.other_team.id)
        
        # 업무 title 변경 여부 확인
        self.assertEqual(response.data['title'], 'Patch Valid Task Title')
        
        # 업무 content 변경 여부 확인
        self.assertEqual(response.data['content'], 'Patch Task Content')

        # subtasks는 4건이 남아야함
        self.assertEqual(len(response.data['subtasks']), 4)
       
        # subtask1 team_id 변경 여부 확인 (is_complete=True)
        matching_subtask = next((subtask for subtask in response.data['subtasks'] if subtask.get('id') == subtask1.id), None)
        self.assertEqual(matching_subtask.get('team_id'), self.team.id)

        # subtask2 team_id 변경 여부 확인 (is_complete=False)
        matching_subtask = next((subtask for subtask in response.data['subtasks'] if subtask.get('id') == subtask2.id), None)
        self.assertEqual(matching_subtask.get('team_id'), self.other_team.id)

        # subtask3가 남아 있는지 확인 (is_complete=True)
        subtask_ids = [subtask['id'] for subtask in response.data['subtasks']]
        self.assertIn(subtask3.id, subtask_ids)

        # subtask4가 삭제 됐는지 확인 (is_complete=False)
        self.assertNotIn(subtask4.id, subtask_ids)

        # 생성됐는지 self.team인 새로운 subtasks의 id는 1,2,3,4 둘다 아니어야 함
        origin_subtasks_ids = [subtask1.id, subtask2.id, subtask3.id, subtask4.id]
        missing_subtask_ids = [subtask_id for subtask_id in subtask_ids if subtask_id not in origin_subtasks_ids]
        self.assertEqual(len(missing_subtask_ids), 1)

    def test_patch_task_with_blank_title(self):
        task = Task.objects.create(create_user=self.user, team=self.other_team, title='Other Task', content='Other Content')
        task_id = task.id
        data = {
            'task': {
                'team_id': self.team.id,
                'title': '',  # 빈 문자열
                'content': 'Task Content',
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.patch(f'/v1/api/tasks/{task_id}', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_patch_task_with_blank_content(self):
        task = Task.objects.create(create_user=self.user, team=self.other_team, title='Other Task', content='Other Content')
        task_id = task.id
        data = {
            'task': {
                'team_id': self.team.id,
                'title': 'Valid Task Title',
                'content': '',
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.patch(f'/v1/api/tasks/{task_id}', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_task_with_invalid_team(self):
        task = Task.objects.create(create_user=self.user, team=self.other_team, title='Other Task', content='Other Content')
        task_id = task.id
        data = {
            'task': {
                'team_id': 9999, # 존재하지 않는 팀 ID
                'title': 'Valid Task Title',
                'content': 'Task Content',
                'subtasks': [
                    {'team_id': self.team.id},
                    {'team_id': self.other_team.id},
                ]
            },
        }
        response = self.client.patch(f'/v1/api/tasks/{task_id}', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_patch_task_with_nonexistent_id(self):
        task_id = 99999  # 존재하지 않는 task_id
        response = self.client.patch(f'/v1/api/tasks/{task_id}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_task_from_other_user(self):
        task = Task.objects.create(create_user=self.other_user, team=self.other_team, title='Other Task', content='Other Content')
        task_id = task.id
        response = self.client.patch(f'/v1/api/tasks/{task_id}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class DeleteTaskAPITestCase(APITestCase):
    def setUp(self):
        self.team = Team.objects.create(name='단비')
        self.other_team = Team.objects.create(name='다래')
        self.user = User.objects.create_user(email='testuser', password='testpassword', team=self.team)
        self.user.save()
        self.other_user = User.objects.create_user(email='testuser2', password='testpassword2', team=self.team)
        self.other_user.save()
        self.client.force_authenticate(user=self.user)

    def test_delete_task_with_nonexistent_id(self):
        task_id = 99999  # 존재하지 않는 task_id
        response = self.client.delete(f'/v1/api/tasks/{task_id}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_task_from_other_user(self):
        task = Task.objects.create(create_user=self.other_user, team=self.team, title='Task Title', content='Task Content')
        task_id = task.id
        response = self.client.delete(f'/v1/api/tasks/{task_id}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_delete_task_successfully(self):
        task = Task.objects.create(create_user=self.user, team=self.team, title='Task Title', content='Task Content')
        subtask1 = SubTask.objects.create(team=self.team, task=task)
        subtask2 = SubTask.objects.create(team=self.other_team, task=task)
        task.subtasks.add(subtask1, subtask2)

        task_id = task.id
        response = self.client.delete(f'/v1/api/tasks/{task_id}')
        
        # HTTP 204 No Content를 기대
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # 삭제된 task를 조회해보면 404 Not Found를 기대
        response = self.client.delete(f'/v1/api/tasks/{task_id}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # 해당 task의 subtasks도 모두 삭제되었는지 확인
        subtasks = SubTask.objects.filter(task=task)
        self.assertEqual(subtasks.count(), 0)



