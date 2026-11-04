"""Authenticated delivery of the generated engineering cockpit snapshot."""

from pathlib import Path

from rest_framework.views import APIView

from utils.permissions import permission_required
from utils.response import NotFound, Ok


SNAPSHOT_PATH = Path(__file__).with_name('snapshot.html')


class CockpitSnapshotView(APIView):
    """Return the read-only cockpit HTML to users with dashboard access."""

    permission_classes = [permission_required('system:dashboard:view')]

    def get(self, request):
        try:
            html = SNAPSHOT_PATH.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            return NotFound(message='驾驶舱快照尚未生成')
        return Ok(
            {
                'html': html,
                'generated_at': SNAPSHOT_PATH.stat().st_mtime_ns,
            },
            headers={'Cache-Control': 'private, no-store'},
        )
