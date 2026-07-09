from ..models import Request



class RequestService:

    @staticmethod
    def prune(request):

        expired = request.record.with_financials().filter(
            _due__lte=0)

        if expired.exists():
            request.record.remove(
                *expired
            )
        
        if not request.record.exists():
            request.delete()

        