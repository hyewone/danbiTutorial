from rest_framework import serializers
from .models import Team, User, Task, SubTask
from django.core.validators import EmailValidator, RegexValidator
from rest_framework.validators import UniqueValidator
from django.contrib.auth import password_validation

class TeamSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, required=True)

    class Meta:
        model = Team
        fields = '__all__'

class UserSignUpSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), required=True)
    email = serializers.EmailField(
        validators=[EmailValidator()],
        error_messages={
            'invalid': '올바른 이메일 주소를 입력하세요.',
        }
        , required=True
    )

    password = serializers.CharField(
        write_only=True,
        validators=[password_validation.validate_password],
        error_messages={
            'invalid': '패스워드는 최소 8자 이상, 숫자를 포함하거나 대문자를 포함하거나 소문자를 포함하거나 특수 문자를 포함해야 합니다.',
            'required': '패스워드는 필수 입력 항목입니다.',
        }
        , required=True
    )

    def validate_team(self, value):
        try:
            team = Team.objects.get(id=value)
        except Team.DoesNotExist:
            raise serializers.ValidationError("팀이 존재하지 않습니다.")
        return value

    class Meta:
        model = User
        fields = ['email', 'password', 'team']
        extra_kwargs = {
            'email': {
                'validators': [UniqueValidator(queryset=User.objects.all())],
            },
        }

class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[EmailValidator()],
        error_messages={
            'invalid': '올바른 이메일 주소를 입력하세요.',
        }
        , required=True
    )
    
    password = serializers.CharField(
        write_only=True, required=True
    )

    class Meta:
        model = User
        fields = ['email', 'password']

class SubTaskSerializer(serializers.ModelSerializer):
    team_id = serializers.IntegerField(required=True)
    
    def validate_team_id(self, value):
        try:
            team = Team.objects.get(id=value)
        except Team.DoesNotExist:
            raise serializers.ValidationError("팀이 존재하지 않습니다.")
        return value

    class Meta:
        model = SubTask
        fields = '__all__'
        read_only_fields = ('id', 'is_complete', 'completed_date', 'created_at', 'modified_at', 'task', 'team')

class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'

class TaskReqSerializer(serializers.ModelSerializer):
    subtasks = SubTaskSerializer(many=True)
    team_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    content = serializers.CharField(required=True)

    def validate_team_id(self, value):
        try:
            team = Team.objects.get(id=value)
        except Team.DoesNotExist:
            raise serializers.ValidationError("팀이 존재하지 않습니다.")
        return value 
    
    def validate_title(self, value):
        if not value.strip():  # 빈 문자열인 경우
            raise serializers.ValidationError("제목은 빈 문자열일 수 없습니다.")
        return value

    def validate_content(self, value):
        if not value.strip():  # 빈 문자열인 경우
            raise serializers.ValidationError("내용은 빈 문자열일 수 없습니다.")
        return value

    def create(self, validated_data):
        subtasks_data = validated_data.pop('subtasks')
        task = Task.objects.create(**validated_data)
        for subtask_data in subtasks_data:
            SubTask.objects.create(task=task, **subtask_data)
        return task

    class Meta:
        model = Task
        fields = ['title', 'content', 'team_id', 'subtasks', 'team']

class SubTaskUpdateSerializer(serializers.ModelSerializer):
    team_id = serializers.IntegerField(required=True)
    id = serializers.IntegerField()
    
    def validate_team_id(self, value):
        try:
            team = Team.objects.get(id=value)
        except Team.DoesNotExist:
            raise serializers.ValidationError("팀이 존재하지 않습니다.")
        return value

    class Meta:
        model = SubTask
        fields = '__all__'
        read_only_fields = ('is_complete', 'completed_date', 'created_at', 'modified_at', 'task', 'team')

class TaskUpdateReqSerializer(serializers.ModelSerializer):
    subtasks = SubTaskUpdateSerializer(many=True)
    team_id = serializers.IntegerField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    content = serializers.CharField(required=True)

    def validate_team_id(self, value):
        try:
            team = Team.objects.get(id=value)
        except Team.DoesNotExist:
            raise serializers.ValidationError("팀이 존재하지 않습니다.")
        return value 
    
    def validate_title(self, value):
        if not value.strip():  # 빈 문자열인 경우
            raise serializers.ValidationError("제목은 빈 문자열일 수 없습니다.")
        return value

    def validate_content(self, value):
        if not value.strip():  # 빈 문자열인 경우
            raise serializers.ValidationError("내용은 빈 문자열일 수 없습니다.")
        return value

    def update(self, instance, validated_data):
        # Task 업데이트
        instance.team_id = validated_data.get('team_id', instance.team_id)
        instance.title = validated_data.get('title', instance.title)
        instance.content = validated_data.get('content', instance.content)
        instance.save()

        # SubTask 업데이트
        subtasks_data = validated_data.get('subtasks')
        if subtasks_data:
            subtask_ids_to_keep = [subtask_data.get('id') for subtask_data in subtasks_data if subtask_data.get('id')]
            # 기존 미완료 서브 업무 중 IDs_to_keep 목록에 없는 것들 삭제
            SubTask.objects.filter(task=instance, is_complete=False).exclude(id__in=subtask_ids_to_keep).delete()

            for subtask_data in subtasks_data:
                subtask_id = subtask_data.get('id')
                if subtask_id:
                    subtask = SubTask.objects.get(id=subtask_id, task=instance)
                    # 서브 업무 업데이트 로직 추가
                    if not subtask.is_complete :
                        subtask.team_id = subtask_data.get('team_id')
                        subtask.save()
                else:
                    # 새로운 서브 업무 생성 로직 추가
                    SubTask.objects.create(task=instance, **subtask_data)

        return instance

    class Meta:
        model = Task
        fields = ['title', 'content', 'team_id', 'subtasks', 'team']

