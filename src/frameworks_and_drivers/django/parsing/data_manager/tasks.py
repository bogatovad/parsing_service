from celery import shared_task

from interface_adapters.controlles.content_controller import (
    GetContentTimepadController,
    GetContentTgController,
    GetContentKudaGoController,
)
from interface_adapters.controlles.factory import UseCaseFactory

factory_usecase = UseCaseFactory()
controller_timepad = GetContentTimepadController(usecase_factory=factory_usecase)
controller_tg = GetContentTgController(usecase_factory=factory_usecase)
controller_kuda_go = GetContentKudaGoController(usecase_factory=factory_usecase)


@shared_task
def parsing_data_from_timepad_task():
    controller_timepad.get_content()


@shared_task
def parsing_data_from_tg_task():
    controller_tg.get_content()


@shared_task
def parsing_data_from_kudago_task():
    controller_kuda_go.get_content()


controller_tg.get_content()
