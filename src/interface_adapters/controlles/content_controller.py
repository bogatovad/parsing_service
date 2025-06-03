from interface_adapters.controlles.exeptions import RunUsecaseException
from interface_adapters.controlles.factory import UseCaseFactory
import os
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "frameworks_and_drivers.django.parsing.parsing.settings"
)


class GetContentTimepadController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from Timepad sources"""
        logger.info("Starting Timepad content parsing")
        try:
            self.usecase_factory.get_timepad_content_usecase().execute()
            logger.info("Successfully finished Timepad content parsing")
            return True
        except Exception as e:
            logger.error(f"Error in Timepad parser: {str(e)}", exc_info=True)
            raise RunUsecaseException(f"Error in Timepad parser: {str(e)}")


class GetContentTgController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from Tg sources"""
        logger.info("Starting Telegram content parsing")
        try:
            self.usecase_factory.get_tg_content_usecase().execute()
            logger.info("Successfully finished Telegram content parsing")
            return True
        except Exception as e:
            logger.error(f"Error in TG parser: {str(e)}", exc_info=True)
            raise RunUsecaseException(f"Error in TG parser: {str(e)}")


class GetContentKudaGoController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from KudaGo sources"""
        logger.info("Starting KudaGo content parsing")
        try:
            self.usecase_factory.get_kuda_go_content_usecase().execute()
            logger.info("Successfully finished KudaGo content parsing")
            return True
        except Exception as e:
            logger.error(f"Error in KudaGo parser: {str(e)}", exc_info=True)
            raise RunUsecaseException(f"Error in KudaGo parser: {str(e)}")


class GetContentVKController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from VK sources"""
        logger.info("Starting VK content parsing")
        try:
            self.usecase_factory.get_vk_content_usecase().execute()
            logger.info("Successfully finished VK content parsing")
            return True
        except Exception as e:
            logger.error(f"Error in VK parser: {str(e)}", exc_info=True)
            raise RunUsecaseException(f"Error in VK parser: {str(e)}")


class PlacesController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from Places sources"""
        logger.info("Starting Places content parsing")
        try:
            self.usecase_factory.get_places_content_usecase().execute()
            logger.info("Successfully finished Places content parsing")
            return True
        except Exception as e:
            logger.error(f"Error in Places parser: {str(e)}", exc_info=True)
            raise RunUsecaseException(f"Error in Places parser: {str(e)}")
