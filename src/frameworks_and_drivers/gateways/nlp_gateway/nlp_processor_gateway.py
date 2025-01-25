from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import NLPProcessorBase


class NLPProcessor(NLPProcessorBase):
    def __init__(self, *args, **kwargs) -> None:
        pass

    def process(self, text: str) -> dict:
        return {}
