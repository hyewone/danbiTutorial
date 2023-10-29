from django.db.models import Q
from wink.models import Task, SubTask, Team, User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from wink.serializers import TaskSerializer, TaskReqSerializer, SubTaskSerializer, TeamSerializer, UserSignUpSerializer, UserLoginSerializer, TaskUpdateReqSerializer, SubTaskUpdateSerializer
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

class TasksView(APIView):

    @swagger_auto_schema(
        operation_id='업무 리스트 조회', 
        responses={200: TaskSerializer(many=True)}
    )
    def get(self, request):
        user_team = request.user.team
        team_tasks = Task.objects.filter(team=user_team).distinct()

        other_tasks = Task.objects.exclude(team=user_team).filter(
            Q(subtasks__team=user_team)
        ).distinct()
        
        unique_tasks = (team_tasks | other_tasks).distinct().order_by('-created_at')

        tasks_serializer = TaskSerializer(unique_tasks, many=True)
        return Response(tasks_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='업무 생성', 
        request_body=TaskReqSerializer,
        responses={200: TaskSerializer}
    )
    def post(self, request):
        create_user = request.user
        task_serializer = TaskReqSerializer(data=request.data['task'])
        
        task_valid = task_serializer.is_valid()

        if task_valid:
            # Task 저장
            task = task_serializer.save(create_user=create_user)
            task_serializer = TaskSerializer(task)
            return Response(task_serializer.data, status=status.HTTP_201_CREATED)
        
        task_errors = task_serializer.errors if not task_valid else None
        return Response({'task_errors': task_errors}, status=status.HTTP_400_BAD_REQUEST)


class TaskView(APIView):
    @swagger_auto_schema(
        operation_id='업무 수정', 
        request_body=TaskUpdateReqSerializer,
        responses={200: TaskSerializer}
    )
    def patch(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        create_user = request.user

        # 권한 체크
        if task.create_user != create_user:
            return Response({'error': '업무 작성자만 수정할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)

        # 수정할 데이터 가져오기
        task_serializer = TaskUpdateReqSerializer(task, data=request.data['task'], partial=True)
       
        task_valid = task_serializer.is_valid()

        if task_valid:
            updated_task = task_serializer.save()
            return Response(TaskSerializer(updated_task).data, status=status.HTTP_200_OK)
            
        task_errors = task_serializer.errors if not task_valid else None
        return Response({'task_errors': task_errors}, status=status.HTTP_400_BAD_REQUEST)
   
    @swagger_auto_schema(
        operation_id='업무 삭제', 
    )
    def delete(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        create_user = request.user

        if task.create_user != create_user:
            return Response({'error': '업무 작성자만 수정할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        task.delete()

        return Response({'message': '업무 삭제 성공'}, status=status.HTTP_204_NO_CONTENT)
        

class SubTaskView(APIView):
    @swagger_auto_schema(
        operation_id='서브 업무 조회', 
        responses={200: SubTaskSerializer}
    )
    def get(self, request, subtask_id):
        subtask_id = get_object_or_404(Task, id=subtask_id)
        subtask_serializer = SubTaskSerializer(subtask_id)
        return Response(subtask_serializer.data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(
        operation_id='서브 업무 수정', 
        responses={200: SubTaskSerializer}
    )
    def patch(self, request, subtask_id):
        subtask = get_object_or_404(SubTask, id=subtask_id)
        is_complete = request.data.get('is_complete')
        subtask_team = subtask.team
        current_user_team = request.user.team
        
        if is_complete is not None:
            if current_user_team == subtask_team:
                subtask.is_complete = is_complete
                subtask.completed_date = timezone.now()
                subtask.save()

                # 상위 Task의 SubTask 체크
                task = subtask.task
                all_subtasks_completed = task.subtask.filter(is_complete=False).count() == 0
                
                if all_subtasks_completed:
                    task.is_complete = True
                    task.completed_date = timezone.now()
                    task.save()
                else:
                    task.is_complete = False
                    task.completed_date = None
                    task.save()

                return Response({'message': 'SubTask 완료 상태 업데이트 완료'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': '하위 업무에 속한 팀만 완료 상태를 변경할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'is_complete 필드가 제공되지 않았습니다.'}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_id='서브 업무 삭제', 
    )
    def delete(self, request, subtask_id):
        subtask = get_object_or_404(SubTask, id=subtask_id)
        task = get_object_or_404(Task, id=subtask.task)
        current_user = request.user
        
        if current_user == task.create_user:
            if subtask.is_complete:
                return Response({'error': '완료된 SubTask는 삭제할 수 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                subtask.delete()
                return Response({'message': 'SubTask 삭제 성공'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': '상위 업무의 작성자만 하위 업무를 삭제할 수 있습니다.'}, status=status.HTTP_403_FORBIDDEN)
        

class TeamsView(APIView):
    @swagger_auto_schema(
        operation_id='팀 리스트 조회', 
    )
    def get(self, request):
        teams = Team.objects.all()
        teams_serializer = TeamSerializer(teams, many=True)
        return Response(teams_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id='팀 생성', 
    )
    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignUpView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id='회원 가입',
        tags=['users'],
        request_body=UserSignUpSerializer,
        responses={
            201: openapi.Response(
                description='회원 가입 성공',
            ),
            400: openapi.Response(
                description='잘못된 요청 또는 데이터 유효성 검사 실패',
            ),
        }
    )
    def post(self, request):
        serializer = UserSignUpSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = make_password(serializer.validated_data['password'])
            team = serializer.validated_data['team']
            # serializer.validated_data['password'] = make_password(password)
            # user = serializer.save()
            user = User.objects.create_user(username=email, password=password, team=team)

            return Response({'user_id': user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id='로그인',
        tags=['users'],
        request_body=UserLoginSerializer,
        responses={
            201: openapi.Response(
                description='로그인 성공',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'accessToken': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='액세스 토큰'
                        ),
                        'refreshToken': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='리프레시 토큰'
                        ),
                    }
                )
            ),
            400: openapi.Response(
                description='잘못된 요청 또는 데이터 유효성 검사 실패',
            ),
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # 인증
            user = authenticate(request, username=email, password=password)

            # 인증 성공
            if user is not None:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                return Response({'access_token': access_token, 'refresh_token': refresh_token}, status=status.HTTP_200_OK)
            # 인증 실패
            else:
                return Response({'error': '인증 실패'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
