import synapseclient
from synapseclient import Table

syn = synapseclient.Synapse()
syn.login()


def submit_vote_to_synapse(model_a, model_b, vote, table_id="syn68561482"):
    try:
        schema = syn.get(table_id)
        print(
            f"[submit_vote_to_synapse] model_a={model_a}, model_b={model_b}, vote={vote}")

        row = [model_a, model_b, vote]

        table = Table(schema, [row])
        syn.store(table)
        print("✅ Vote submitted successfully using ordered values.")
    except Exception as e:
        print(f"[Synapse Submission Error] {e}")
