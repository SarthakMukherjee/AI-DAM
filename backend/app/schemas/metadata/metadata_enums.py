from enum import Enum

class AssetStatus(str, Enum):
    DRAFT="draft"
    APPROVED="approved"
    ARCHIVED="archived"
    PENDING_REVIEW="pending_review"
    REJECTED="rejected"

class AssetTypes(str, Enum):
    IMAGE="image"
    VIDEO="video"
    PDF="pdf"
    DOCUMENT="document"

class DomainType(str, Enum):
    AI="AI"
    STAFFING="staffing"
    MARKETING="marketing"
    SALES="sales"
    FINANCE="finance"
    HR="hr"
    OPERATIONS="operations"
    HEALTHCARE="healthcare"

class UseCaseTypes(str, Enum):
    WEBSITE="website"
    CAMPAIGN="campaign"
    SALES="sales"
    SOCIAL_MEDIA="social_media"

class AudienceType(str, Enum):
    B2B="b2b"
    ENTERPRISE="enterprise"
    STARTUP="startup"

class FunnelStage(str, Enum):
    AWARENESS="awareness"
    CONSIDERATION="consideration"
    CONVERSION="conversion"

class ToneType(str, Enum):
    PROFESSIONAL="professional"
    CASUAL="casual"
    TECHNICAL="technical"

