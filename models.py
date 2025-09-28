from datetime import datetime
from typing import Optional
import hashlib
from pydantic import BaseModel, Field, EmailStr, validator

def hash_pii(value: str) -> str:
    """Hash PII data using SHA-256."""
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

class SurveySubmission(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=13, le=120)
    consent: bool = Field(..., description="Must be true to accept")
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=1000)
    user_agent: Optional[str] = Field(None, max_length=1000)
    submission_id: Optional[str] = Field(None, description="Unique submission identifier")

    @validator("comments")
    def _strip_comments(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("consent")
    def _must_consent(cls, v):
        if v is not True:
            raise ValueError("consent must be true")
        return v
    
    @validator("submission_id", always=True)
    def _compute_submission_id(cls, v, values):
        """Compute submission_id from email + current date/hour if not provided."""
        if v is not None:
            return v
        
        # Get email from values
        email = values.get('email')
        if email is None:
            return v
        
        # Get current date and hour in YYYYMMDDHH format
        now = datetime.now()
        date_hour = now.strftime('%Y%m%d%H')
        
        # Hash email + date_hour
        combined = f"{email}{date_hour}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    
        
#Good example of inheritance
class StoredSurveyRecord(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    hashed_email: str = Field(..., description="SHA-256 hash of email")
    hashed_age: str = Field(..., description="SHA-256 hash of age")
    consent: bool = Field(..., description="Must be true to accept")
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=1000)
    user_agent: Optional[str] = Field(None, max_length=1000)
    received_at: datetime
    ip: str
    submission_id: str = Field(..., description="Unique submission identifier")
    
    @classmethod
    def from_submission(cls, submission: SurveySubmission, received_at: datetime, ip: str) -> 'StoredSurveyRecord':
        """Create a StoredSurveyRecord from a SurveySubmission, hashing PII fields."""
        return cls(
            name=submission.name,
            hashed_email=hash_pii(submission.email),
            hashed_age=hash_pii(submission.age),
            consent=submission.consent,
            rating=submission.rating,
            comments=submission.comments,
            user_agent=submission.user_agent,
            received_at=received_at,
            ip=ip,
            submission_id=submission.submission_id
        )
