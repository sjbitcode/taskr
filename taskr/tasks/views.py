from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import enums
from config.paginators import CustomPagination
from .models import Task, TaskEventLog
from .serializers import (
    TaskSerializer,
    TaskStatusSerializer,
    TaskEventLogSerializer
)


User = get_user_model()


class Checkpoint(APIView):

    def get(self, request, format=None):
        response_data = {
            'message': "This is a test message"
        }
        return Response(response_data, status=status.HTTP_200_OK)


class TaskListCreate(generics.GenericAPIView):
    '''
    View to list all tasks if method is GET,
    or create a task if method is POST.

    * Requires token authentication.
    '''
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get(self, request, format=None):
        '''
        Returns paginated list of all tasks.
        '''
        tasks = Task.objects.all()

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request):
        '''
        Create a task.
        '''
        task_serializer = TaskSerializer(data=request.data)

        if task_serializer.is_valid():
            task = Task(**task_serializer.validated_data)
            task.reporter = request.user
            task.save()

            # Create TaskEventLog instance for create event.
            log = TaskEventLog(
                task=task,
                user=request.user,
                event=enums.EVENT_CREATED,
                description='Task created.'
            )
            log.save()

            return Response(
                TaskSerializer(task).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            task_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class TaskDetail(APIView):
    '''
    Get, update or delete a task.

    * Requires token authentication.
    '''
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        '''
        Get task detail.
        '''
        task = get_object_or_404(Task, pk=pk)
        task_serializer = TaskSerializer(task)

        return Response(task_serializer.data)

    def put(self, request, pk):
        '''
        Update task.
        '''
        task = get_object_or_404(Task, pk=pk)
        task_serializer = TaskSerializer(
            instance=task,
            data=request.data,
            partial=True
        )

        if task_serializer.is_valid():
            task_serializer.save()

            # Create TaskEventLog instance for update event.
            log = TaskEventLog(
                task=task,
                user=request.user,
                event=enums.EVENT_EDITED,
                description='Task edited.'
            )
            log.save()

            return Response(task_serializer.data)

        return Response(
            task_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        '''
        Delete task.
        '''
        task = get_object_or_404(Task, pk=pk)
        task.delete()

        return Response(
            {'id': '{}'.format(pk)},
            status=status.HTTP_200_OK
        )


class TaskAssign(APIView):
    '''
    Assign a task to a User.

    * Requires token authentication.
    '''
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        user = request.data.get('user')

        # Check if user is an empty string.
        try:
            user = get_object_or_404(User, pk=user)
        except ValueError:
            user = None

        # Check if user same as existing assignee.
        if task.assignee == user:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            task.assignee = user
            task.save()

            # Create TaskEventLog instance for assign event.
            log = TaskEventLog(
                task=task,
                user=request.user,
                event=enums.EVENT_ASSIGNED,
                description='Task assigned to {}.'.format(user)
            )
            log.save()

            return Response(
                TaskSerializer(task).data
            )


class TaskChangeStatus(APIView):
    '''
    Change the status of a Task.

    * Requires token authentication.
    '''
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        task_serializer = TaskStatusSerializer(
            task,
            data=request.data,
            partial=True
        )

        if task_serializer.is_valid():

            # Check if new status same as existing status.
            if task_serializer.validated_data.get('status') == task.status:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                task = task_serializer.save()

                # Create TaskEventLog instance for status change event.
                log = TaskEventLog(
                    task=task,
                    user=request.user,
                    event=enums.EVENT_STATUS_CHANGED,
                    description='Task status changed to "{}".'.format(
                        task_serializer.data
                    )
                )
                log.save()

                return Response(TaskSerializer(task).data)

        return Response(
            task_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class TaskEventLogList(APIView):
    '''
    Get event logs for a task.

    * Requires token authentication.
    '''
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)

        logs = TaskEventLog.objects.select_related().filter(task=task)

        logs_serializer = TaskEventLogSerializer(logs, many=True)

        return Response(logs_serializer.data)


class UserReports(APIView):
    '''
    Reporting task info for a user.

    Counts tasks for each user that are
      - created
      - assigned
      - completed
      - incompleted

    * Requires token authentication.
    '''
    permission_classes = (IsAuthenticated,)

    def get(self, request, username):
        user = get_object_or_404(User, username=username)

        # Get queryset of tasks that user has created or assigned to.
        tasks = Task.objects.all()

        # Count the created tasks for a user.
        created_count = tasks.filter(reporter=user).count()

        # Count the assigned, completed, incompleted tasks for a user.
        # Derived from queryset of assigned tasks.
        assigned_tasks = tasks.filter(assignee=user)
        assigned_count = assigned_tasks.count()
        completed_count = assigned_tasks.filter(
            status=enums.STATUS_DONE
        ).count()
        incompleted_count = assigned_tasks.filter(
            status__in=[enums.STATUS_TODO, enums.STATUS_IN_PROGRESS]
        ).count()

        # Create response object.
        response = {}
        response['created'] = created_count
        response['assigned'] = assigned_count
        response['completed'] = completed_count
        response['incompleted'] = incompleted_count

        return Response(response, status=status.HTTP_200_OK)
