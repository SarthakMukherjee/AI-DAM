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

    BANNER="banner"
    BROCHURE="brochure"
    CASE_STUDY="case study"
    LOGO="logo"
    SOCIAL_CREATIVE="social creative"
    PITCH_DECK="pitch deck"
    BRAND_GUIDLINE="brand guideline"
    CAMPAIGN_FILE="campaign file"
    TESTIMONIAL="testimonial"

class DomainType(str, Enum):
    AI="AI"
    STAFFING="Staffing"
    MARKETING="Marketing"
    SALES="Sales"
    FINANCE="Finance"
    HR="HR"
    OPERATIONS="Operations"
    HEALTHCARE="Healthcare"
    TECH="Tech"
    DESIGN="Design"

class UseCaseTypes(str, Enum):
    EMAIL="email"
    PRESENTATION="presentation"
    WEBSITE="website"
    CAMPAIGN="campaign"
    SALES="sales"
    SOCIAL_MEDIA="social media"
    ADVERTISEMENT="advertisement"

class AudienceType(str, Enum):
    B2B="b2b"
    ENTERPRISE="enterprise"
    STARTUP="startup"
    CONSUMER="consumer"
    PARTNER="partner"


class FunnelStage(str, Enum):
    AWARENESS="awareness"
    CONSIDERATION="consideration"
    CONVERSION="conversion"

class ToneType(str, Enum):
    PROFESSIONAL="professional"
    CASUAL="casual"
    TECHNICAL="technical"
    FORMAL="formal"
    FRIENDLY="friendly"
    CREATIVE="creative"


class UsageRightsType(str, Enum):
    INTERNAL_ONLY  = "Internal Only"
    LICENSED       = "Licensed"
    PUBLIC_DOMAIN  = "Public Domain"
    RESTRICTED     = "Restricted"
    ROYALTY_FREE   = "Royalty Free"
    CREATIVE_COMMONS = "Creative Commons"
