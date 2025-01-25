from celery import shared_task

from interface_adapters.controlles.content_controller import GetContentController
from interface_adapters.controlles.factory import UseCaseFactory

factory_usecase = UseCaseFactory()
controller = GetContentController(usecase_factory=factory_usecase)


@shared_task
def example_task():
    controller.get_content()
