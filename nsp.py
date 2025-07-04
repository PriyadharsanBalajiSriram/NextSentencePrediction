!pip install numpy==1.26.4
!pip install transformers torch datasets matplotlib scikit-learn

import torch
from transformers import BertTokenizer, BertForNextSentencePrediction, Trainer, TrainingArguments
from datasets import Dataset
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score

sentences = [
    ("The quick brown fox jumps over the lazy dog.", "The dog was not amused.", 1),
    ("The quick brown fox jumps over the lazy dog.", "I love eating pizza.", 0),
    ("She opened the door.", "She saw her friend standing there.", 1),
    ("She opened the door.", "The sky was blue.", 0),
    ("He went to the store.", "He bought some groceries.", 1),
    ("He went to the store.", "It started raining heavily.", 0)
]

dataset = Dataset.from_dict({
    "sentence1": [s[0] for s in sentences],
    "sentence2": [s[1] for s in sentences],
    "label": [s[2] for s in sentences]
})

train_test_split = dataset.train_test_split(test_size=0.2)
train_dataset = train_test_split['train']
test_dataset = train_test_split['test']

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')


def tokenize_function(examples):
    return tokenizer(
        examples['sentence1'],
        examples['sentence2'],
        truncation=True,
        padding='max_length',
        max_length=128
    )

train_dataset = train_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

train_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])
test_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'label'])

model = BertForNextSentencePrediction.from_pretrained('bert-base-uncased')

training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    save_strategy="epoch",
)


def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
    compute_metrics=compute_metrics
)


trainer.train()

eval_results = trainer.evaluate()
print(f"\nEvaluation Results: {eval_results}")

predictions = trainer.predict(test_dataset)
probs = torch.softmax(torch.tensor(predictions.predictions), dim=1).numpy()

for i in range(len(test_dataset)):
    plt.bar(['Next Sentence', 'Not Next Sentence'], probs[i])
    plt.title(f"Sample {i+1}: True Label = {test_dataset[i]['label']}")
    plt.ylabel("Probability")
    plt.show()

