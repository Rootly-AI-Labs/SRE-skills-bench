# Reliability-bench: The Test Suite Benchmarking LLM Accuracy on SRE Tasks ⚗️

Think of **Reliability-bench** as the *SWE-bench for SREs*. 

This benchmark evaluates Large Language Models on tasks commonly performed by Site Reliability Engineers, helping reliability practitioners choose the right model for the job, whether it's powering IDE assistants, automating operational workflows, or improving incident response.

[image of graph showing accuracy vs price]()

## Findings

The table below represents the average accuracy of each model across all SRE-related tasks** included in the benchmark.

| Model        | % Accuracy | Avg. $ / 1k tokens | Org      | Date       |
|--------------|------------|--------------------|----------|------------|
| MODEL_NAME   | XX%        | $X.XX              | IMG | YYYY-MM-DD |
| MODEL_NAME   | XX%        | $X.XX              | IMG | YYYY-MM-DD |
| MODEL_NAME   | XX%        | $X.XX              | IMG | YYYY-MM-DD |


## Methodology

Reliability-bench evaluates models on tasks that represent real, day-to-day SRE responsibilities.  
Each task category includes multiple test cases with expected outputs, graded programmatically or via structured evaluation. For each test, we open-source 40% of the entire dataset, available on our [HF repo]().

### Test one

Explanation of the methodology...

### Test two
Explanation of the methodology...



## Getting Started

To reproduce our results or use our benchmark to benchmark other models.

```
# Create a virtual environment and install OpenBench
uv venv
source .venv/bin/activate
uv pip install openbench


#Set your API key (any provider!)
export GROQ_API_KEY=your_key  # or OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

#Run Rootly’s benchmark
bench eval gmcq --model "groq/llama-3.1-8b-instant" --T subtask=mastodon
```

## Where we share our findings

|Conference Name| Date|
| ER @ NeurIPS | Dec 2-7 2025 |
| New In ML @ ICML 2025, KnowFM @ ACL 2025 | July 13-19 2025 |

## 🔗 About the Rootly AI Labs
The On-call Burnout Detector is built with ❤️ by the [Rootly AI Labs](https://rootly.com/ai-labs) for engineering teams everywhere. The Rootly AI Labs is a fellow-led community designed to redefine reliability engineering. We develop innovative prototypes, create open-source tools, and produce research that's shared to advance the standards of operational excellence. We want to thank Anthropic, Google Cloud, and Google DeepMind for their support.
