import asyncio
import json
from api.document_upload import doctor_graph


async def test_emergency():
    print("\n" + "=" * 50)
    print("TEST 1: EMERGENCY CASE")
    print("=" * 50)
    res = await doctor_graph.ainvoke({
        "prompt": "I have sudden severe crushing chest pain radiating to my left arm and jaw and I can't breathe",
        "chat_id": "test-emergency-01",
        "prompt_type": "text",
        "file": None,
        "audio_file": None,
    })
    print(f"is_medical: {res.get('is_medical')}")
    print(f"is_emergency: {res.get('is_emergency')}")
    print(f"urgency_level: {res.get('urgency_level')}")
    print(f"Triage Flags: {json.dumps(res.get('triage', {}).get('flags', []), indent=2)}")
    print(f"Response Preview:\n{res.get('final_response', '')[:250]}...")
    assert res.get("is_emergency") is True, "Emergency should be True"
    assert res.get("urgency_level") == "emergency", "Urgency should be emergency"
    print(">>> TEST 1 PASSED!")


async def test_non_medical():
    print("\n" + "=" * 50)
    print("TEST 2: NON-MEDICAL QUERY")
    print("=" * 50)
    res = await doctor_graph.ainvoke({
        "prompt": "Can you help me write a Python script to sort a list using quicksort?",
        "chat_id": "test-non-med-01",
        "prompt_type": "text",
        "file": None,
        "audio_file": None,
    })
    print(f"is_medical: {res.get('is_medical')}")
    print(f"Response: {res.get('response')}")
    assert res.get("is_medical") is False, "is_medical should be False"
    print(">>> TEST 2 PASSED!")


async def test_routine_clinical():
    print("\n" + "=" * 50)
    print("TEST 3: ROUTINE CLINICAL CONSULTATION")
    print("=" * 50)
    res = await doctor_graph.ainvoke({
        "prompt": "I have had a mild dry cough and slight fatigue for 3 days. I took one Crocin yesterday.",
        "chat_id": "test-routine-01",
        "prompt_type": "text",
        "file": None,
        "audio_file": None,
    })
    print(f"is_medical: {res.get('is_medical')}")
    print(f"is_emergency: {res.get('is_emergency')}")
    print(f"urgency_level: {res.get('urgency_level')}")
    
    diff = res.get("differential", {})
    print(f"Primary Impression: {diff.get('primary_impression')}")
    print("Possible Causes:")
    for c in diff.get("possible_causes", []):
        print(f" - {c.get('name')} (Likelihood: {c.get('likelihood')})")

    meds = res.get("medicines", [])
    print(f"Medicines Normalized: {json.dumps(meds, indent=2)}")

    safety = res.get("safety_review", {})
    print(f"Safety Review: {json.dumps(safety, indent=2)}")

    final_structured = res.get("final_structured_response", {})
    print(f"Disclaimer present: {'disclaimer' in final_structured}")
    print(f"Book results count: {len(res.get('book_results', []))}")
    print(f"Web results count: {len(res.get('web_results', []))}")
    assert res.get("is_medical") is True
    assert len(diff.get("possible_causes", [])) > 0, "Should have differential diagnoses"
    print(">>> TEST 3 PASSED!")


async def main():
    await test_emergency()
    await test_non_medical()
    await test_routine_clinical()
    print("\nALL 3 PIPELINE TESTS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())

