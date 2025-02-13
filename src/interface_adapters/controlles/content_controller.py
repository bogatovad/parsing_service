from interface_adapters.controlles.exeptions import RunUsecaseException
from interface_adapters.controlles.factory import UseCaseFactory
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frameworks_and_drivers.django.parsing.parsing.settings')
from frameworks_and_drivers.django.parsing.data_manager.models import Content, Tags


class GetContentController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from different sources"""
        try:
            content_tg = self.usecase_factory.get_tg_content_usecase().execute()
            #content_yandex = self.usecase_factory.get_yandex_afisha_content_usecase().execute()
            #content_kuda_go = self.usecase_factory.get_kuda_go_content_usecase().execute()
            #content_timepad = self.usecase_factory.get_timepad_content_usecase().execute()
            print(f"{content_tg=}")
            #print(f"{content_yandex=}")
            #print(f"{content_kuda_go=}")
            #print(f"{content_timepad=}")
            return True
        except Exception as e:
            raise RunUsecaseException

