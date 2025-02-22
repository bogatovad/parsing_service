from interface_adapters.controlles.exeptions import RunUsecaseException
from interface_adapters.controlles.factory import UseCaseFactory
import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "frameworks_and_drivers.django.parsing.parsing.settings"
)


class GetContentController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from different sources"""
        try:
            self.usecase_factory.get_timepad_content_usecase().execute()
            self.usecase_factory.get_tg_content_usecase().execute()
            self.usecase_factory.get_kuda_go_content_usecase().execute()
            return True
        except Exception:
            raise RunUsecaseException
