import glob
import json
from random import Random

import spacy
from spacy.training import Example


def training(nlp):
    mynlp = spacy.blank("pl")
    textcat = mynlp.add_pipe("textcat")
    textcat.add_label("TOC")  # Table of Contents
    textcat.add_label("Other")  # Table of Contents
    textcat.add_label("MNumbers")  # Table of Contents

    train_data = []
    for jfile in glob.glob("utils/dataset/*.json"):
        with open(jfile, 'r', encoding='utf-8') as file:
            train_data.extend(json.load(file))

    # Trening
    optimizer = mynlp.begin_training()
    for i in range(8):  # epoki
        losses = {}
        Random().shuffle(train_data)
        for cell in train_data:
            doc = mynlp.make_doc(cell["text"])
            example = Example.from_dict(doc, {"cats": cell["cats"]})
            mynlp.update([example], losses=losses, sgd=optimizer)
        print(losses)
    nlp.add_pipe("textcat", name="textcat_2", source=mynlp)

    return nlp