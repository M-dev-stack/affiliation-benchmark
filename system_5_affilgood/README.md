# System 5: AffilGood

This system uses [AffilGood](https://github.com/sirisacademic/affilgood) (Duran-Silva et al., 2024) for affiliation string to ROR ID matching.

## Setup

1. Install AffilGood:
```bash
pip install -e ".[all]"
```

2. **Important Windows fix**: In `affilgood/components/entity_linking/index.py` line 530, change:
```python
texts = json.loads((index_dir / "faiss_texts.json").read_text())
```
to:
```python
texts = json.loads((index_dir / "faiss_texts.json").read_text(encoding="utf-8"))
```
This fixes a Windows charmap encoding error when loading the FAISS index.

## Configuration

- `enable_entity_linking=True`
- `reranker=None`
- `threshold=0.5`

## Run

```bash
python system_5_affilgood/run_affilgood.py
```

## Output

Results are saved to `system_5_affilgood/affilgood_results.csv` with columns:
- `an`: publication ID
- `ror_id`: predicted ROR ID (without `https://ror.org/` prefix), empty if no match found
