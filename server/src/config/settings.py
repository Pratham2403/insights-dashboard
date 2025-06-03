"""
Configuration settings for the the Sprinklr Insights Dashboard Application.

This File consists of the all the configuration settings that are required for the application to run.
"""

import os
from typing import Dict, Optional, Any, List, Union
from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
import time

class Settings(BaseSettings):
    """
    Provides Configuration Settings for the Sprinklr Insights Dashboard Application.
    Loaded from the environment variables or a .env file.
    """
    
    #Sprinklr API Configuration
    SPRINKLR_DATA_API_URL: str = Field(
        default="https://space-prod0.sprinklr.com/ui/rest/reports/query",
    )
    SPRINKLR_COOKIES: Optional[Union[Dict[str, str], str]] = "SPR_STICKINESS=1748840825.348.203.951301|935c7dcb81a00314ea56a3b1f4989107; JSESSIONID=076FFDE0076CCED31E26B429CDFB7007; ajs_anonymous_id=98d0793c-d4c8-41b5-9d50-10c22349f814; user.env.type=ENTERPRISE; connect.sid=s%3A6qR2HVc7gyq4gtiFVnaaB2PaZKY7LAoY.UDeSCYxlUoLawG5JYdZ3I%2F6GadL0TknXXP3ZH6da4kw; SPR_AT=SjFRazB6WE1DcUJ3aEZMM0Q5Qmpy; connect.token=eyJ2M1Nlc3Npb25VcGRhdGVkIjoidHJ1ZSIsImFjY2Vzc1Rva2VuIjoiZXlKaGJHY2lPaUpTVXpJMU5pSjkuZXlKemRXSWlPaUpCWTJObGMzTWdWRzlyWlc0Z1IyVnVaWEpoZEdWa0lFSjVJRk53Y21sdWEyeHlJaXdpWTJ4cFpXNTBTV1FpT2pFd01EQXdNRFExTURrc0lteHZaMmx1VFdWMGFHOWtJam9pVTBGTlRDSXNJbTkwWVVsa0lqb2lOamd6WkRNeE56UTFObVl5TnpNMk9XUm1aakV4WWpWaUlpd2lhWE56SWpvaVUxQlNTVTVMVEZJaUxDSjBlWEFpT2lKS1YxUWlMQ0oxYzJWeVNXUWlPakV3TURBME5qSXhNellzSW5WMWFXUWlPaUk0TkRFMllUVm1aaTFsTmpkakxUUmhORFV0WWpnMU9TMDJORFE1TmpaaU9ERTVOR1U2TVRjMU5UVTBPVFF4TnpnM09UQTRNeUlzSW1GMVpDSTZJbE5RVWtsT1MweFNJaXdpYm1KbUlqb3hOelE0T0RNNU5qSXhMQ0p6WTI5d1pTSTZXeUpTUlVGRUlpd2lWMUpKVkVVaVhTd2ljMlZ6YzJsdmJsUnBiV1Z2ZFhRaU9qRXdNVEk0TUN3aWNHRnlkRzVsY2tsa0lqbzVNREEwTENKbGVIQWlPakUzTkRreE1EQXdNakVzSW1GMWRHaFVlWEJsSWpvaVUxQlNYMHRGV1Y5UVFWTlRYMHhQUjBsT0lpd2lkRzlyWlc1VWVYQmxJam9pUVVORFJWTlRJaXdpYVdGMElqb3hOelE0T0RRd09ESXhMQ0pxZEdraU9pSnpjSEpwYm10c2NpSXNJbTFwWTNKdlUyVnlkbWxqWlNJNkluTndjaUo5Lkd3enlrdzdWWmVVQXh0UDJ6dW5sSFlvM2dGemcxMnBFbVRXMzExY05kZEJDdmVDc05xUUJybTduRURtZW9MZE5GTEI2YVVKSS1uU1pETGcwa1AwREFQOExYbFQzUm44dWJvRmlPNzEtZDVmc01fNFVOZVU5Mmh6TDc2NFMzSDVIOHNzMVVrQ3FJRFN3bFhFUXd6ZzBNYjBLcGVNaE1felFtMUNmV1pBZUFUVm5oTzRJeTktWlROMzIwa3A2WXJkTmhCR251cDBXM3hfRlJLV0o3czcxNWFMYnQxMTZuNWVSOTh5LVQ5Mk8tMURjTXFIN3MzcC1JX1l3cWdTQW8zNDI2SHdTcG9XaHk3anRaQzMtT3YtVHZCa1c4WWt5eFJ1ZkJ2OHdSRUJsQkxHejh3MFE1cTNzSXZMX2VhaVZpSHg5RnBod3BXcThmekQ0aDZhOXB2MWIxUSJ9.DuQgEHpWKL5/AklMAnZb7MypFzD1KI46EnCOSIFdzEw; sess-exp-time=Wed, 4 Jun 2025 10:23:05 GMT"
    SPRINKLR_CSRF_TOKEN: Optional[str] = None
    SPRINKLR_USER_CONTEXT: Optional[str] = None
    SPRINKLR_DASHBOARD_ID: Optional[str] = None
    SPRINKLR_WIDGET_ID: Optional[str] = None
    
    
    
    #LLM Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    DEFAULT_MODEL: str = "gemini-2.0-flash"
    
    
    #Memory Configuration
    MEMORY_TYPE: str = "file_system"
    MEMORY_PATH: str = "./conversation_memory"


settings = Settings()
