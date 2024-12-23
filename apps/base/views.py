import zoneinfo

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Home"
        return context


class UpdateTimezoneView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        timezone = request.POST.get("timezone")

        # Validate the timezone
        if timezone not in zoneinfo.available_timezones():
            return JsonResponse(
                {"status": "error", "message": "Invalid timezone"}, status=400
            )

        # Update user's timezone
        request.user.timezone = timezone
        request.user.save(update_fields=["timezone"])

        return JsonResponse(
            {"status": "success", "message": "Timezone updated successfully"}
        )

    # Optionally handle unauthorized users trying to access this view
    def handle_no_permission(self):
        return JsonResponse(
            {
                "status": "error",
                "message": "You must be logged in to update your timezone",
            },
            status=403,
        )
