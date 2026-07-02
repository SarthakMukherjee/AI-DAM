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
    CASE_STUDY="case_study"
    LOGO="logo"
    SOCIAL_CREATIVE="social_creative"
    PITCH_DECK="pitch_deck"
    BRAND_GUIDLINE="brand_guideline"
    CAMPAIGN_FILE="campaign_file"
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
    SOCIAL_MEDIA="social_media"
    ADVERTISEMENT="advertisment"

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

