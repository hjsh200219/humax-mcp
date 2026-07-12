"""Structured error codes per PRD §4 error tables."""

from __future__ import annotations


class HumaxMCPError(Exception):
    code: str = "UNKNOWN"

    def __init__(self, message: str, *, code: str | None = None, **details) -> None:
        super().__init__(message)
        if code:
            self.code = code
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {
            "status": "error",
            "success": False,
            "error": {"code": self.code, "message": self.message, **self.details},
        }


def _make(code: str) -> type[HumaxMCPError]:
    return type(code, (HumaxMCPError,), {"code": code})


FileNotFound = _make("FILE_NOT_FOUND")
SheetNotFound = _make("SHEET_NOT_FOUND")
InvalidColumn = _make("INVALID_COLUMN")
InvalidCompany = _make("INVALID_COMPANY")
InvalidPagination = _make("INVALID_PAGINATION")
TokenLimitExceeded = _make("TOKEN_LIMIT_EXCEEDED")
EmptyResult = _make("EMPTY_RESULT")
FileLocked = _make("FILE_LOCKED")
SchemaMismatch = _make("SCHEMA_MISMATCH")

ParseError = _make("PARSE_ERROR")
SubtotalNotFound = _make("SUBTOTAL_NOT_FOUND")

BackupFailed = _make("BACKUP_FAILED")
InvalidCell = _make("INVALID_CELL")
WritePermissionDenied = _make("WRITE_PERMISSION_DENIED")
VerificationFailed = _make("VERIFICATION_FAILED")
TooManyUpdates = _make("TOO_MANY_UPDATES")
OverwriteOriginalForbidden = _make("OVERWRITE_ORIGINAL_FORBIDDEN")

StructureMismatch = _make("STRUCTURE_MISMATCH")

InvalidMonth = _make("INVALID_MONTH")
RateSumViolation = _make("RATE_SUM_VIOLATION")
RateSumNot100 = _make("RATE_SUM_NOT_100")
InvalidRate = _make("INVALID_RATE")
CCBasisNotFound = _make("CC_BASIS_NOT_FOUND")

ApiKeyMissing = _make("API_KEY_MISSING")
ApiRequestFailed = _make("API_REQUEST_FAILED")
InvalidDateFormat = _make("INVALID_DATE_FORMAT")
FutureDate = _make("FUTURE_DATE")
NoDataForDate = _make("NO_DATA_FOR_DATE")
FallbackExhausted = _make("FALLBACK_EXHAUSTED")
ApiRateLimit = _make("API_RATE_LIMIT")
InvalidCurrency = _make("INVALID_CURRENCY")

TemplateNotFound = _make("TEMPLATE_NOT_FOUND")
TemplateMalformed = _make("TEMPLATE_MALFORMED")
BindingNotFound = _make("BINDING_NOT_FOUND")
BackupNotFound = _make("BACKUP_NOT_FOUND")
RestoreFailed = _make("RESTORE_FAILED")
