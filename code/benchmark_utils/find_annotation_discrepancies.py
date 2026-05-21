import json


def filter_discrepancies(file00_path, file01_path, output_path):
    with (
        open(file00_path, "r", encoding="utf-8") as f0,
        open(file01_path, "r", encoding="utf-8") as f1,
    ):
        data00 = json.load(f0)
        data01 = json.load(f1)

    discrepancies = []

    for obj0, obj1 in zip(data00, data01):
        rating00 = obj0.get("harmfulness_rating")
        rating01 = obj1.get("harmfulness_rating")

        if rating00 != rating01:
            new_obj = obj0.copy()

            # Clean up the old key and add the versioned keys
            new_obj.pop("harmfulness_rating", None)
            new_obj["harmfulness_rating_00"] = rating00
            new_obj["harmfulness_rating_01"] = rating01

            discrepancies.append(new_obj)

    # Save the filtered results
    with open(output_path, "w", encoding="utf-8") as f_out:
        json.dump(discrepancies, f_out, indent=4, ensure_ascii=False)

    print(f"Found {len(discrepancies)} differences.")
    print(f"Discrepancies saved to: {output_path}")


filter_discrepancies(
    "en_annotated_00.json", "en_annotated_01.json", "discrepancies.json"
)
