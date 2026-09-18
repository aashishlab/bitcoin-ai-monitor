import random
import pandas as pd


def generate_entities_and_wallets(num_entities=20, total_wallets=100, seed=42):
    """
    Generate ground-truth entity to wallet mapping.

    Args:
        num_entities (int): Number of entities to generate (default 20).
        total_wallets (int): Total number of wallets to generate (default 100).
        seed (int): Random seed for reproducibility.

    Returns:
        tuple: (entity_wallet_df, entities, wallets, entity_to_wallets)
    """
    random.seed(seed)

    entities = [f"entity_{i:03d}" for i in range(1, num_entities + 1)]
    wallets = [f"wallet_{i:03d}" for i in range(1, total_wallets + 1)]

    entity_to_wallets = {e: [] for e in entities}
    unassigned_wallets = wallets.copy()

    # Assign at least 2 wallets to each entity initially
    for entity in entities:
        for _ in range(2):
            if unassigned_wallets:
                w = unassigned_wallets.pop(0)
                entity_to_wallets[entity].append(w)

    # Distribute remaining wallets randomly ensuring max 8 per entity
    while unassigned_wallets:
        entity = random.choice(entities)
        if len(entity_to_wallets[entity]) < 8:
            w = unassigned_wallets.pop(0)
            entity_to_wallets[entity].append(w)

    rows = []
    for entity_id, wallet_list in entity_to_wallets.items():
        for wallet_id in wallet_list:
            rows.append({"wallet_id": wallet_id, "entity_id": entity_id})

    rows.sort(key=lambda x: x["wallet_id"])
    entity_wallet_df = pd.DataFrame(rows)

    return entity_wallet_df, entities, wallets, entity_to_wallets
