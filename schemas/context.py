from pydantic import BaseModel, Field

class ContextResult(BaseModel):

    is_medical: bool = Field(description="Indicates if the context is medical or not")
    structured_prompt: str = Field(description="A complete coherent representation of the user's request, "
            "including all relevant information from the prompt and document.")
    response: str|None = Field(
        default=None,
        description=("Response to return immediately when the request is not medical."))
        
