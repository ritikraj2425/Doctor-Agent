# Doctor AI Agent - OOP + LangChain Diagram Canvas

This canvas describes the system as Python classes, methods, inheritance, and runtime connections.

## 1. Complete Class Diagram

```mermaid
classDiagram
    direction LR

    class DoctorAgentApp {
        +FastAPI app
        +include_routes()
        +configure_dependencies()
        +startup()
    }

    class ChatController {
        -DoctorAgentOrchestrator orchestrator
        +chat(request: ChatRequest) DoctorAgentResponse
        +stream_chat(request: ChatRequest) AsyncIterator
    }

    class DocumentController {
        -DocumentService document_service
        +upload_document(file, user_id) DocumentUploadResponse
        +index_document(document_id) IndexResponse
    }

    class VoiceController {
        -SpeechService speech_service
        -DoctorAgentOrchestrator orchestrator
        +voice_chat(audio, user_id) DoctorAgentResponse
    }

    class DoctorAgentOrchestrator {
        -AgentRegistry agents
        -StateGraph graph
        +build_graph() CompiledGraph
        +handle_case(request: DoctorAgentRequest) DoctorAgentResponse
        +route_after_triage(state: DoctorAgentState) str
        +route_after_intake(state: DoctorAgentState) str
    }

    class AgentRegistry {
        +IntakeAgent intake
        +MedicalTriageAgent triage
        +DocumentRagAgent document_rag
        +WebResearchAgent web_research
        +RootCauseAgent root_cause
        +MedicineVerifierAgent medicine_verifier
        +PurchaseLinkAgent purchase_links
        +SafetyGuardAgent safety_guard
        +ResponseComposerAgent response_composer
    }

    class BaseAgent {
        <<abstract>>
        #BaseChatModel llm
        #list~BaseTool~ tools
        #PromptTemplate prompt
        +run(state: DoctorAgentState)* DoctorAgentState
        #structured_call(input, schema) BaseModel
        #log_decision(state, decision) None
    }

    class IntakeAgent {
        -PromptBuilder prompt_builder
        -TranslationService translation_service
        +run(state) DoctorAgentState
        +extract_symptoms(message) list~Symptom~
        +extract_patient_context(message) PatientContext
        +ask_missing_questions(case) list~str~
    }

    class MedicalTriageAgent {
        -SafetyRuleEngine safety_rules
        +run(state) DoctorAgentState
        +classify_relevance(case) TriageDecision
        +detect_emergency(case) EmergencySignal
        +detect_medication_relation(case) bool
    }

    class DocumentRagAgent {
        -MedicalRetriever retriever
        -CitationService citation_service
        +run(state) DoctorAgentState
        +search_user_documents(case) list~AgentFinding~
        +search_medical_kb(case) list~AgentFinding~
        +rank_findings(findings) list~AgentFinding~
    }

    class WebResearchAgent {
        -TrustedWebSearchTool web_search
        +run(state) DoctorAgentState
        +build_queries(case, rag_findings) list~str~
        +search_trusted_sources(queries) list~WebFinding~
        +summarize_sources(results) list~AgentFinding~
    }

    class RootCauseAgent {
        +run(state) DoctorAgentState
        +generate_differential(case, findings) list~PossibleCause~
        +build_safe_care_options(causes) list~CareStep~
        +prepare_doctor_questions(case) list~str~
    }

    class MedicineVerifierAgent {
        -MedicineLookupTool medicine_lookup
        -MedicationService medication_service
        +run(state) DoctorAgentState
        +extract_medicine_names(text) list~str~
        +normalize_to_generic(names) list~Medicine~
        +check_interactions(medicines, context) list~MedicationWarning~
        +verify_prescription_status(medicine) VerificationResult
    }

    class PurchaseLinkAgent {
        -PharmacySearchTool pharmacy_search
        +run(state) DoctorAgentState
        +find_purchase_links(medicines, location) list~PurchaseOption~
        +filter_unsafe_links(options) list~PurchaseOption~
        +attach_prescription_notice(options) list~PurchaseOption~
    }

    class SafetyGuardAgent {
        -SafetyRuleEngine safety_rules
        +run(state) DoctorAgentState
        +review_response(draft) SafetyReview
        +block_unsafe_advice(draft) bool
        +rewrite_with_disclaimer(draft) str
    }

    class ResponseComposerAgent {
        +run(state) DoctorAgentState
        +compose_summary(state) str
        +compose_citations(findings) list~Citation~
        +compose_final_json(state) DoctorAgentResponse
    }

    class DocumentService {
        -DocumentRepository document_repo
        -DocumentParser parser
        -VectorStore vector_store
        +save_upload(file, user_id) Document
        +extract_text(document_id) ExtractedDocument
        +index_document(document_id) None
        +get_user_documents(user_id) list~Document~
    }

    class SpeechService {
        -STTClient stt
        -TTSClient tts
        +transcribe(audio, language_hint) Transcript
        +synthesize(text, language) AudioResponse
    }

    class TranslationService {
        +detect_language(text) str
        +translate_to_english(text) str
        +translate_from_english(text, language) str
    }

    class PromptBuilder {
        +build_intake_prompt(input) str
        +build_triage_prompt(case) str
        +build_rag_query(case) str
        +build_final_answer_prompt(state) str
    }

    class MedicalRetriever {
        -VectorStore vector_store
        -Embeddings embeddings
        +retrieve_user_docs(query, user_id) list~DocumentChunk~
        +retrieve_medical_kb(query) list~DocumentChunk~
        +hybrid_search(query, filters) list~DocumentChunk~
    }

    class SafetyRuleEngine {
        +check_emergency_red_flags(case) list~SafetyFlag~
        +check_dosage_request(message) bool
        +check_prescription_risk(medicines) list~SafetyFlag~
        +final_output_review(response) SafetyReview
    }

    class MedicationService {
        +normalize_name(name) Medicine
        +check_duplicate_therapy(medicines) list~MedicationWarning~
        +check_allergy_conflict(medicines, allergies) list~MedicationWarning~
        +check_interactions(medicines) list~MedicationWarning~
    }

    class CitationService {
        +make_citation(chunk) Citation
        +merge_citations(findings) list~Citation~
        +validate_citations(response) bool
    }

    class ConversationRepository {
        +save_message(session_id, message) None
        +get_history(session_id) list~Message~
        +save_state(case_id, state) None
    }

    class DocumentRepository {
        +create(document) Document
        +get(document_id) Document
        +list_by_user(user_id) list~Document~
        +delete(document_id) None
    }

    class AuditRepository {
        +log_agent_step(case_id, agent_name, input, output) None
        +log_safety_event(case_id, flags) None
    }

    BaseAgent <|-- IntakeAgent
    BaseAgent <|-- MedicalTriageAgent
    BaseAgent <|-- DocumentRagAgent
    BaseAgent <|-- WebResearchAgent
    BaseAgent <|-- RootCauseAgent
    BaseAgent <|-- MedicineVerifierAgent
    BaseAgent <|-- PurchaseLinkAgent
    BaseAgent <|-- SafetyGuardAgent
    BaseAgent <|-- ResponseComposerAgent

    DoctorAgentApp --> ChatController
    DoctorAgentApp --> DocumentController
    DoctorAgentApp --> VoiceController
    ChatController --> DoctorAgentOrchestrator
    VoiceController --> SpeechService
    VoiceController --> DoctorAgentOrchestrator
    DocumentController --> DocumentService
    DoctorAgentOrchestrator --> AgentRegistry
    DoctorAgentOrchestrator --> ConversationRepository
    DoctorAgentOrchestrator --> AuditRepository

    AgentRegistry --> IntakeAgent
    AgentRegistry --> MedicalTriageAgent
    AgentRegistry --> DocumentRagAgent
    AgentRegistry --> WebResearchAgent
    AgentRegistry --> RootCauseAgent
    AgentRegistry --> MedicineVerifierAgent
    AgentRegistry --> PurchaseLinkAgent
    AgentRegistry --> SafetyGuardAgent
    AgentRegistry --> ResponseComposerAgent

    IntakeAgent --> PromptBuilder
    IntakeAgent --> TranslationService
    MedicalTriageAgent --> SafetyRuleEngine
    DocumentRagAgent --> MedicalRetriever
    DocumentRagAgent --> CitationService
    WebResearchAgent --> TrustedWebSearchTool
    MedicineVerifierAgent --> MedicationService
    MedicineVerifierAgent --> MedicineLookupTool
    PurchaseLinkAgent --> PharmacySearchTool
    SafetyGuardAgent --> SafetyRuleEngine

    DocumentService --> DocumentRepository
    DocumentService --> MedicalRetriever
    MedicalRetriever --> VectorStore
```

## 2. Main Runtime Flow

```mermaid
flowchart TD
    A[User starts session] --> B{Input type}
    B -->|Medical PDF/report| C[DocumentController.upload_document]
    B -->|Voice Hindi/English| D[VoiceController.voice_chat]
    B -->|Text any language| E[ChatController.chat]

    C --> F[DocumentService.save_upload]
    F --> G[DocumentService.extract_text]
    G --> H[DocumentService.index_document]
    H --> I[DoctorAgentOrchestrator.handle_case]

    D --> J[SpeechService.transcribe]
    J --> I
    E --> I

    I --> K[IntakeAgent.run]
    K --> L[Build MedicalCase]
    L --> M{Missing critical info?}
    M -->|Yes| N[ResponseComposerAgent asks follow-up]
    M -->|No| O[MedicalTriageAgent.run]

    O --> P{Triage route}
    P -->|Emergency| Q[Immediate emergency guidance]
    P -->|Non-medical| R[Out-of-scope response]
    P -->|Medical routine/urgent| S[Parallel research]

    S --> T[DocumentRagAgent searches uploaded docs + disease/symptom KB]
    S --> U[WebResearchAgent searches trusted internet sources]

    T --> V[RootCauseAgent.run]
    U --> V
    V --> W[MedicineVerifierAgent.run]
    W --> X{Medicine purchase lookup allowed?}
    X -->|Yes| Y[PurchaseLinkAgent.run]
    X -->|No| Z[Skip purchase links]
    Y --> AA[ResponseComposerAgent.run]
    Z --> AA
    AA --> AB[SafetyGuardAgent.run]
    AB --> AC{Safe final answer?}
    AC -->|Needs rewrite| AA
    AC -->|Approved| AD[Return DoctorAgentResponse]
```

## 3. LangGraph State Machine

```mermaid
stateDiagram-v2
    [*] --> Intake
    Intake --> FollowUpNeeded: missing required context
    Intake --> Triage: enough context

    FollowUpNeeded --> [*]

    Triage --> EmergencyResponse: emergency red flags
    Triage --> NonMedicalResponse: not medical
    Triage --> Research: valid medical concern

    EmergencyResponse --> SafetyReview
    NonMedicalResponse --> SafetyReview

    state Research {
        [*] --> ParallelResearch
        ParallelResearch --> DocumentRAG
        ParallelResearch --> WebResearch
        DocumentRAG --> MergeFindings
        WebResearch --> MergeFindings
        MergeFindings --> [*]
    }

    Research --> RootCauseSynthesis
    RootCauseSynthesis --> MedicineVerification
    MedicineVerification --> PurchaseLinks: verified medicine names found
    MedicineVerification --> ComposeResponse: no medicine lookup needed
    PurchaseLinks --> ComposeResponse
    ComposeResponse --> SafetyReview
    SafetyReview --> ComposeResponse: unsafe or unsupported claim
    SafetyReview --> FinalResponse: approved
    FinalResponse --> [*]
```

## 4. Sequence Diagram - One User Query

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI Controller
    participant Orch as DoctorAgentOrchestrator
    participant Intake as IntakeAgent
    participant Triage as MedicalTriageAgent
    participant RAG as DocumentRagAgent
    participant Web as WebResearchAgent
    participant Root as RootCauseAgent
    participant Med as MedicineVerifierAgent
    participant Buy as PurchaseLinkAgent
    participant Safe as SafetyGuardAgent
    participant DB as Repositories

    User->>API: text/voice/document + symptoms
    API->>Orch: DoctorAgentRequest
    Orch->>Intake: run(state)
    Intake-->>Orch: MedicalCase + normalized prompt
    Orch->>DB: save case state

    Orch->>Triage: run(state)
    Triage-->>Orch: TriageDecision

    alt emergency
        Orch->>Safe: review emergency response
        Safe-->>API: urgent escalation response
    else non-medical
        Orch->>Safe: review out-of-scope response
        Safe-->>API: safe refusal/redirect
    else medical concern
        par document knowledge
            Orch->>RAG: search symptoms in uploaded docs + medical PDFs
            RAG-->>Orch: cited document findings
        and web research
            Orch->>Web: search trusted sources
            Web-->>Orch: cited web findings
        end
        Orch->>Root: synthesize possible causes + care steps
        Root-->>Orch: PossibleCause list + next steps
        Orch->>Med: verify medicine names/interactions
        Med-->>Orch: verified medicines + warnings
        Orch->>Buy: find safe purchase links
        Buy-->>Orch: purchase options with prescription notices
        Orch->>Safe: final review
        Safe-->>API: approved DoctorAgentResponse
    end

    API-->>User: final answer
```

## 5. Data Classes And Relationships

```mermaid
classDiagram
    direction LR

    class DoctorAgentRequest {
        +str session_id
        +str user_id
        +str message
        +InputType input_type
        +list~str~ document_ids
        +PatientContext patient_context
    }

    class DoctorAgentState {
        +DoctorAgentRequest request
        +MedicalCase case
        +TriageDecision triage
        +list~AgentFinding~ document_findings
        +list~AgentFinding~ web_findings
        +list~PossibleCause~ possible_causes
        +list~Medicine~ medicines
        +list~PurchaseOption~ purchase_options
        +SafetyReview safety_review
        +DoctorAgentResponse response
    }

    class PatientContext {
        +str user_id
        +int age
        +str sex
        +str location
        +list~str~ allergies
        +list~str~ known_conditions
        +list~str~ current_medications
    }

    class MedicalCase {
        +str case_id
        +str language
        +list~Symptom~ symptoms
        +str duration
        +str severity
        +list~str~ uploaded_document_ids
        +PatientContext patient_context
    }

    class Symptom {
        +str name
        +str body_part
        +str duration
        +str severity
        +list~str~ modifiers
    }

    class TriageDecision {
        +bool is_medical
        +bool medication_related
        +UrgencyLevel urgency_level
        +Route route
        +str reason
        +list~SafetyFlag~ flags
    }

    class AgentFinding {
        +str source_name
        +SourceType source_type
        +str summary
        +list~str~ evidence
        +float confidence
        +list~Citation~ citations
    }

    class Medicine {
        +str brand_name
        +str generic_name
        +str drug_class
        +bool prescription_required
        +VerificationStatus verification_status
    }

    class PurchaseOption {
        +str medicine_name
        +str vendor
        +str url
        +str price
        +bool prescription_required
        +float trust_score
    }

    class DoctorAgentResponse {
        +str case_id
        +UrgencyLevel urgency
        +str summary
        +list~PossibleCause~ possible_causes
        +list~AgentFinding~ findings
        +list~Medicine~ medicines
        +list~PurchaseOption~ purchase_options
        +list~str~ next_steps
        +list~str~ doctor_questions
        +str disclaimer
    }

    DoctorAgentRequest --> PatientContext
    DoctorAgentState --> DoctorAgentRequest
    DoctorAgentState --> MedicalCase
    DoctorAgentState --> TriageDecision
    DoctorAgentState --> AgentFinding
    DoctorAgentState --> Medicine
    DoctorAgentState --> PurchaseOption
    DoctorAgentState --> DoctorAgentResponse
    MedicalCase --> PatientContext
    MedicalCase --> Symptom
    TriageDecision --> SafetyFlag
    AgentFinding --> Citation
    DoctorAgentResponse --> AgentFinding
    DoctorAgentResponse --> Medicine
    DoctorAgentResponse --> PurchaseOption
```

## 6. Inheritance And Composition Rules

```mermaid
flowchart LR
    A[BaseAgent abstract class] --> B[IntakeAgent]
    A --> C[MedicalTriageAgent]
    A --> D[DocumentRagAgent]
    A --> E[WebResearchAgent]
    A --> F[RootCauseAgent]
    A --> G[MedicineVerifierAgent]
    A --> H[PurchaseLinkAgent]
    A --> I[SafetyGuardAgent]
    A --> J[ResponseComposerAgent]

    K[DoctorAgentOrchestrator] -->|has one| L[AgentRegistry]
    L -->|contains| B
    L -->|contains| C
    L -->|contains| D
    L -->|contains| E
    L -->|contains| F
    L -->|contains| G
    L -->|contains| H
    L -->|contains| I
    L -->|contains| J

    D -->|uses| M[MedicalRetriever]
    M -->|uses| N[VectorStore]
    B -->|uses| O[TranslationService]
    C -->|uses| P[SafetyRuleEngine]
    I -->|uses| P
    G -->|uses| Q[MedicationService]
    H -->|uses| R[PharmacySearchTool]
```

## 7. Method-Level Call Flow

```mermaid
flowchart TD
    A[DoctorAgentOrchestrator.handle_case] --> B[DoctorAgentState.from_request]
    B --> C[IntakeAgent.run]
    C --> C1[IntakeAgent.extract_symptoms]
    C --> C2[IntakeAgent.extract_patient_context]
    C --> C3[IntakeAgent.ask_missing_questions]
    C --> D[MedicalTriageAgent.run]
    D --> D1[MedicalTriageAgent.detect_emergency]
    D --> D2[MedicalTriageAgent.classify_relevance]
    D --> D3[MedicalTriageAgent.detect_medication_relation]
    D --> E{route_after_triage}

    E -->|research| F[DocumentRagAgent.run]
    E -->|research| G[WebResearchAgent.run]
    E -->|emergency| H[ResponseComposerAgent.compose_final_json]
    E -->|stop| H

    F --> F1[search_user_documents]
    F --> F2[search_medical_kb]
    F --> F3[rank_findings]

    G --> G1[build_queries]
    G --> G2[search_trusted_sources]
    G --> G3[summarize_sources]

    F3 --> I[RootCauseAgent.run]
    G3 --> I
    I --> I1[generate_differential]
    I --> I2[build_safe_care_options]
    I --> I3[prepare_doctor_questions]

    I --> J[MedicineVerifierAgent.run]
    J --> J1[extract_medicine_names]
    J --> J2[normalize_to_generic]
    J --> J3[check_interactions]
    J --> J4[verify_prescription_status]

    J --> K[PurchaseLinkAgent.run]
    K --> K1[find_purchase_links]
    K --> K2[filter_unsafe_links]
    K --> K3[attach_prescription_notice]

    K --> H
    H --> L[SafetyGuardAgent.run]
    L --> L1[review_response]
    L --> L2{safe?}
    L2 -->|no| L3[rewrite_with_disclaimer]
    L3 --> H
    L2 -->|yes| M[return DoctorAgentResponse]
```

## 8. Python Class Skeleton

```python
from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel, Field


class PatientContext(BaseModel):
    user_id: str
    age: int | None = None
    sex: str | None = None
    location: str | None = None
    allergies: list[str] = Field(default_factory=list)
    known_conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)


class Symptom(BaseModel):
    name: str
    body_part: str | None = None
    duration: str | None = None
    severity: str | None = None
    modifiers: list[str] = Field(default_factory=list)


class MedicalCase(BaseModel):
    case_id: str
    language: str
    symptoms: list[Symptom]
    duration: str | None = None
    severity: str | None = None
    uploaded_document_ids: list[str] = Field(default_factory=list)
    patient_context: PatientContext


class TriageDecision(BaseModel):
    is_medical: bool
    medication_related: bool
    urgency_level: Literal["emergency", "urgent", "routine", "non_medical"]
    route: Literal["emergency", "research", "ask_followup", "stop"]
    reason: str


class DoctorAgentState(BaseModel):
    request: "DoctorAgentRequest"
    case: MedicalCase | None = None
    triage: TriageDecision | None = None
    document_findings: list["AgentFinding"] = Field(default_factory=list)
    web_findings: list["AgentFinding"] = Field(default_factory=list)
    medicines: list["Medicine"] = Field(default_factory=list)
    purchase_options: list["PurchaseOption"] = Field(default_factory=list)
    response: "DoctorAgentResponse | None" = None


class BaseAgent(ABC):
    def __init__(self, llm, tools=None):
        self.llm = llm
        self.tools = tools or []

    @abstractmethod
    async def run(self, state: DoctorAgentState) -> DoctorAgentState:
        pass

    async def structured_call(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        chain = self.llm.with_structured_output(schema)
        return await chain.ainvoke(prompt)


class IntakeAgent(BaseAgent):
    def __init__(self, llm, prompt_builder, translation_service):
        super().__init__(llm)
        self.prompt_builder = prompt_builder
        self.translation_service = translation_service

    async def run(self, state: DoctorAgentState) -> DoctorAgentState:
        prompt = self.prompt_builder.build_intake_prompt(state.request)
        state.case = await self.structured_call(prompt, MedicalCase)
        return state


class MedicalTriageAgent(BaseAgent):
    def __init__(self, llm, safety_rules):
        super().__init__(llm)
        self.safety_rules = safety_rules

    async def run(self, state: DoctorAgentState) -> DoctorAgentState:
        emergency_flags = self.safety_rules.check_emergency_red_flags(state.case)
        if emergency_flags:
            state.triage = TriageDecision(
                is_medical=True,
                medication_related=False,
                urgency_level="emergency",
                route="emergency",
                reason="Emergency red flags detected.",
            )
            return state

        prompt = f"Classify this medical case: {state.case.model_dump_json()}"
        state.triage = await self.structured_call(prompt, TriageDecision)
        return state


class DoctorAgentOrchestrator:
    def __init__(self, agents):
        self.agents = agents
        self.graph = self.build_graph()

    def build_graph(self):
        from langgraph.graph import StateGraph, END

        graph = StateGraph(DoctorAgentState)
        graph.add_node("intake", self.agents.intake.run)
        graph.add_node("triage", self.agents.triage.run)
        graph.add_node("document_rag", self.agents.document_rag.run)
        graph.add_node("web_research", self.agents.web_research.run)
        graph.add_node("root_cause", self.agents.root_cause.run)
        graph.add_node("medicine", self.agents.medicine_verifier.run)
        graph.add_node("purchase_links", self.agents.purchase_links.run)
        graph.add_node("response", self.agents.response_composer.run)
        graph.add_node("safety", self.agents.safety_guard.run)

        graph.set_entry_point("intake")
        graph.add_edge("intake", "triage")
        graph.add_conditional_edges(
            "triage",
            self.route_after_triage,
            {
                "emergency": "response",
                "stop": "response",
                "research": "document_rag",
            },
        )
        graph.add_edge("document_rag", "web_research")
        graph.add_edge("web_research", "root_cause")
        graph.add_edge("root_cause", "medicine")
        graph.add_edge("medicine", "purchase_links")
        graph.add_edge("purchase_links", "response")
        graph.add_edge("response", "safety")
        graph.add_edge("safety", END)
        return graph.compile()

    def route_after_triage(self, state: DoctorAgentState) -> str:
        return state.triage.route

    async def handle_case(self, request):
        state = DoctorAgentState(request=request)
        final_state = await self.graph.ainvoke(state)
        return final_state.response
```

## 9. Recommended Connections In Code

```mermaid
flowchart TD
    A[main.py dependency container] --> B[LLM Factory]
    A --> C[Vector Store Factory]
    A --> D[Tool Factory]
    A --> E[Repository Factory]
    A --> F[Service Factory]
    A --> G[Agent Factory]

    B --> H[BaseChatModel]
    C --> I[Chroma/Qdrant/pgvector]
    D --> J[Search + Medicine + Pharmacy Tools]
    E --> K[ConversationRepository + DocumentRepository + AuditRepository]
    F --> L[DocumentService + SpeechService + TranslationService + MedicationService]
    G --> M[AgentRegistry]

    H --> M
    J --> M
    L --> M
    M --> N[DoctorAgentOrchestrator]
    K --> N
    N --> O[FastAPI Controllers]
```

## 10. Build Order

```mermaid
flowchart LR
    A[Define Pydantic domain models] --> B[Create BaseAgent]
    B --> C[Build IntakeAgent]
    C --> D[Build MedicalTriageAgent]
    D --> E[Create LangGraph orchestrator]
    E --> F[Add DocumentService + RAG]
    F --> G[Add WebResearchAgent]
    G --> H[Add RootCauseAgent]
    H --> I[Add MedicineVerifierAgent]
    I --> J[Add PurchaseLinkAgent]
    J --> K[Add SafetyGuardAgent]
    K --> L[Expose FastAPI endpoints]
    L --> M[Write tests and evals]
```
