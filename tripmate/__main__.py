from .agent import TripMateAgent


if __name__ == "__main__":
    agent = TripMateAgent()
    print("TripMate AI Assistant")
    print("Type 'exit' to quit.\n")
    while True:
        query = input("You> ")
        if not query or not query.strip():
            print("Please enter a valid travel question.")
            continue
        if query.strip().lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        print("\nAssistant> ")
        try:
            print(agent.answer(query))
        except ValueError:
            print("Please enter a valid travel question.")
            continue
        print("\nReasoning trace:")
        for step in agent.trace:
            print(f"- {step}")
        agent.trace.clear()
