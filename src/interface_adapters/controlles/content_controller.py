from interface_adapters.controlles.factory import UseCaseFactory


class GetContentController:
    def __init__(self, usecase_factory: UseCaseFactory):
        self.usecase_factory = usecase_factory

    def get_content(self) -> bool:
        """Get content from different sources"""
        try:
            content_tg = self.usecase_factory.get_tg_content_usecase().execute()
            content_yandex = self.usecase_factory.get_yandex_afisha_content_usecase().execute()
            content_kuda_go = self.usecase_factory.get_kuda_go_content_usecase().execute()
            content_timepad = self.usecase_factory.get_timepad_content_usecase().execute()
            print(f"{content_tg=}")
            print(f"{content_yandex=}")
            print(f"{content_kuda_go=}")
            return True
        except Exception as e:
            raise Exception(status_code=400, detail=str(e))

