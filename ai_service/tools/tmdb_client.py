"""Client TMDB tối giản (chỉ thư viện chuẩn) dùng cho công cụ dòng lệnh. KHÔNG dùng khi chạy API/demo.

- Xác thực: Read Access Token qua header Authorization (khóa không nằm trong URL).
  Nếu chỉ có API Key v3 thì phải đưa vào query string; URL đó KHÔNG BAO GIỜ được log,
  mọi thông báo lỗi đều đi qua redact().
- Giãn tốc độ: tối đa 4 lệnh/giây (mặc định). Timeout 15 giây.
- Lỗi 429 / 5xx / lỗi mạng: thử lại tối đa 3 lần, thời gian chờ tăng dần, tôn trọng Retry-After.
- Đếm số lệnh gọi thật (mỗi lần gửi request, kể cả lần thử lại).
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from env_loader import get_tmdb_credential, redact

API_BASE = "https://api.themoviedb.org/3"
MAX_RETRY_AFTER_SEC = 30


class TmdbError(Exception):
    """Lỗi TMDB. Thông điệp đã được che khóa."""


def _default_transport(url, headers, timeout):
    """Trả về (status, headers_dict, body_bytes). Ném HTTPError/URLError khi lỗi."""
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, dict(resp.headers.items()), resp.read()


class TmdbClient:
    def __init__(self, max_per_sec=4, timeout=15, max_retries=3,
                 transport=None, sleep=time.sleep, clock=time.monotonic,
                 credential=None):
        self.min_interval = 1.0 / max_per_sec
        self.timeout = timeout
        self.max_retries = max_retries
        self._transport = transport or _default_transport
        self._sleep = sleep
        self._clock = clock
        self._last_start = None
        self.calls = 0          # số request thực sự đã gửi
        self.log = []           # chỉ ghi path + params (KHÔNG có khóa, KHÔNG có header)
        self.kind, self._secret = credential if credential else get_tmdb_credential()

    def _throttle(self):
        if self._last_start is not None:
            wait = self.min_interval - (self._clock() - self._last_start)
            if wait > 0:
                self._sleep(wait)
        self._last_start = self._clock()

    def _safe(self, text):
        return redact(text, extra_secrets=(self._secret,))

    def get(self, path, params=None):
        if not self._secret:
            raise TmdbError("chưa có khóa TMDB")
        params = dict(params or {})
        query = dict(params)
        headers = {"accept": "application/json"}
        if self.kind == "READ_TOKEN":
            headers["Authorization"] = "Bearer " + self._secret
        else:
            query["api_key"] = self._secret
        url = API_BASE + path + "?" + urllib.parse.urlencode(query)

        last_problem = ""
        for attempt in range(self.max_retries + 1):
            self._throttle()
            self.calls += 1
            status, retry_after, body = None, None, b""
            try:
                status, resp_headers, body = self._transport(url, headers, self.timeout)
            except urllib.error.HTTPError as exc:
                status = exc.code
                resp_headers = dict(exc.headers.items()) if exc.headers else {}
                try:
                    body = exc.read()
                except Exception:
                    body = b""
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_problem = "lỗi mạng: " + self._safe(type(exc).__name__ + " " + str(exc))
                status = None
                resp_headers = {}

            if status is not None and 200 <= status < 300:
                self.log.append({"path": path, "params": params, "status": status})
                try:
                    return json.loads(body.decode("utf-8"))
                except ValueError:
                    raise TmdbError("phản hồi không phải JSON hợp lệ (HTTP %s)" % status)

            if status in (401, 403):
                self.log.append({"path": path, "params": params, "status": status})
                raise TmdbError("HTTP %s: khóa bị từ chối hoặc không đủ quyền" % status)
            if status == 404:
                self.log.append({"path": path, "params": params, "status": status})
                raise TmdbError("HTTP 404: không tìm thấy %s" % path)

            retryable = status is None or status == 429 or (status is not None and status >= 500)
            if status is not None:
                last_problem = "HTTP %s" % status
                if status == 429:
                    retry_after = resp_headers.get("Retry-After") or resp_headers.get("retry-after")
            if not retryable or attempt >= self.max_retries:
                self.log.append({"path": path, "params": params, "status": status})
                raise TmdbError("không thành công sau %d lần gọi: %s" % (attempt + 1, last_problem))

            delay = 2 ** attempt  # 1s, 2s, 4s
            if retry_after:
                try:
                    delay = max(delay, min(float(retry_after), MAX_RETRY_AFTER_SEC))
                except ValueError:
                    pass
            self._sleep(delay)
        raise TmdbError("không thành công: " + last_problem)  # không tới được, để an toàn

