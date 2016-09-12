from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Task, TaskCategory
from .serializers import TaskSerializer

User = get_user_model()


class TasksTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'testuser',
            'testuser@email.com',
            'testuser',
            is_staff=True,
            is_superuser=True
        )

        # Define headers
        self.headers = {
            'content-type': 'application/json',
            'secret-message': 'my-secret-message',
            'HTTP_AUTHORIZATION': 'Token {}'.format(self.user.auth_token.key)
        }

    def create_some_task(self, **kwargs):
        '''
        By default creates a task with
            name = "some task", description = "some description",
            category = "general", priority = "medium", status = "todo",
            reporter = self.user, assignee = None
        '''
        some_task = Task.objects.create(
            name=kwargs.get('name', 'some task'),
            description=kwargs.get('description', 'some description'),
            category=kwargs.get(
                'category',
                TaskCategory.objects.get(name='General')
            ),
            priority=kwargs.get('priority', 3),
            status=kwargs.get('status', 1),
            reporter=kwargs.get('reporter', self.user),
            assignee=kwargs.get('assignee', None)
        )
        return some_task

    def create_another_user(self):
        other_user = User.objects.create_user(
            'dummyuser',
            'dummyemail@email.com',
            'dummyuser',
            is_staff=True,
            is_superuser=True
        )
        return other_user

    def test_get_tasks(self):
        '''
        Test the GET method on TaskListCreate view
        with authorized and unauthorized users.
        '''
        url = reverse('task-list')

        # Check that status code for authorized request is OK.
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that status code for unauthorized request is UNAUTHORIZED.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_tasks(self):
        '''
        Test the POST method on TaskListCreate view.
        Creates a task and check if it exists.
        '''
        url = reverse('task-list')
        data = {
            'name': 'Test Task 1',
            'description': 'Do this task first',
            'category': 1,
            'priority': 3,
            'status': 1,
            'reporter': self.user.pk,
            'assignee': None
        }

        # Check that task is created successfully by authorized user.
        response = self.client.post(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(self.user.created_tasks.count(), 1)

        # Check that task cannot be created by unauthorized user.
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Delete all tasks.
        Task.objects.all().delete()

    def test_get_task_detail(self):
        '''
        Test the GET method on TaskDetail view.
        '''
        task_pk = 11
        url = reverse('task-detail', kwargs={'pk': task_pk})

        # Checks if not possible to get task that does not exist.
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Checks if possible to get task that does exist.
        task = self.create_some_task()
        url = reverse('task-detail', kwargs={'pk': task.pk})

        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response data.
        expected_response = TaskSerializer(task).data
        self.assertEqual(response.data, expected_response)

        # Checks that a task cannot be retrieved by unauthorized user.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Delete all tasks.
        Task.objects.all().delete()

    def test_update_task_detail(self):
        '''
        Test the PUT method on TaskDetail view.
        Only update a task's name, description, category, priority.
        '''
        task_pk = 129
        url = reverse('task-detail', kwargs={'pk': task_pk})
        data = {
            'name': 'a new and improved name!',
            'description': 'a new and improved description!',
            'category': 2,
            'priority': 4
        }

        # Checks if not possible to update task that does not exist.
        response = self.client.put(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Checks if possible to update task that exists.
        task = self.create_some_task()
        url = reverse('task-detail', kwargs={'pk': task.pk})

        response = self.client.put(url, data, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that you cannot update reporter, assignee, status field.
        other_user = self.create_another_user()

        # ... read-only fields cannot be changed.
        data2 = {
            'reporter': other_user.pk,
            'assignee': other_user.pk,
            'status': 3
        }

        # ... getting updated task data from previous response.
        task_data = response.data

        # ... tries to update task with read-only fields
        response = self.client.put(url, data2, **self.headers)
        self.assertEqual(response.data, task_data)

        # Checks that a task cannot be updated by unauthorized user.
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Delete all tasks.
        Task.objects.all().delete()

    def test_delete_task_detail(self):
        '''
        Test the DELETE method on TaskDetail view.
        '''
        task_pk = 71
        url = reverse('task-detail', kwargs={'pk': task_pk})

        # Checks if not possible to delete task that does not exist.
        response = self.client.delete(url, **self.headers)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        task = self.create_some_task()
        url = reverse('task-detail', kwargs={'pk': task.pk})

        # Checks that a task cannot be deleted by unauthorized user.
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # ... check that the created task objects exist
        self.assertEqual(Task.objects.filter(pk=task.pk).exists(), True)

        # Checks if possible to delete a task that exists.
        response = self.client.delete(url, **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Task.objects.filter(pk=task.pk).exists(), False)
