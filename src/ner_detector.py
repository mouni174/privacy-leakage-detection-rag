import spacy

nlp = spacy.load("en_core_web_sm")


def detect_entities(text: str):

    doc = nlp(text)

    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],
        "LOC": [],
        "DATE": [],
        "MONEY": []
    }

    for ent in doc.ents:

        if ent.label_ in entities:

            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)

    return entities