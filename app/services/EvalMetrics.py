import json

class EvalMetrics:
    def __init__(self):
        pass

    async def compute(self, data: list[dict]) -> dict:
        """
        Compute citation recall and precision metrics based on evaluation results.

        Parameters:
            data (list[dict]): Evaluation result containing predicted entailment and provenance.

        Returns:
            dict: Dictionary containing citation_recall, citation_precision,
                and numerator/denominator details.
        """
        print("[DEBUG] EvalMetrics.py Entry")
        if not isinstance(data, list) or not data:
            raise ValueError("Invalid input: expected a non-empty list of dictionaries.")

        total_of_sent = len(data)
        total_entailed = 0
        total_matched = 0
        total_cited = 0
        precision_scores = []

        for entry in data:
            if not isinstance(entry, dict):
                continue

            entailment = entry.get("entailment_prediction", 0)
            citations = set(entry.get("citations", []))
            provenance = set(entry.get("provenance", []))

            if entailment == 1:
                total_entailed += 1

            matched = len(citations & provenance)
            total_matched += matched
            total_cited += len(citations)

            precision_scores.append(matched / len(citations) if citations else 0.0)

        citation_recall = total_entailed / total_of_sent
        citation_precision = sum(precision_scores) / total_of_sent

        return {
            "citation_recall": round(citation_recall, 4),
            "total_entailed": total_entailed,
            "total_of_sent": total_of_sent,
            "citation_precision": round(citation_precision, 4),
            "total_matched_citations": total_matched,
            "total_citations": total_cited,
        }
