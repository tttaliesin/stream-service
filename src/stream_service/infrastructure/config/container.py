from dependency_injector import containers, providers

from ...application.use_cases.stream_use_cases import StreamUseCases
from ...domain.services.stream_service import StreamDomainService
from ..adapters.output.memory_stream_repository import MemoryStreamRepository


class Container(containers.DeclarativeContainer):
    stream_repository = providers.Singleton(MemoryStreamRepository)
    
    stream_domain_service = providers.Factory(
        StreamDomainService,
        stream_repository=stream_repository,
    )
    
    stream_use_cases = providers.Factory(
        StreamUseCases,
        stream_service=stream_domain_service,
    )