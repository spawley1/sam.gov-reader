import anthropic
import json
import logging

logger = logging.getLogger(__name__)

class ClaudeSearch:
    def __init__(self, api_key: str):
        self.client = anthropic.Client(api_key)
        self.model = "claude-3-sonnet-20240229"  # Use the latest model available

    def enhance_query(self, user_query: str) -> str:
        try:
            prompt = f"Enhance the following search query for government contracts: {user_query}\n\nEnhanced query:"
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens_to_sample=100
            )
            return response.completion.strip()
        except Exception as e:
            logger.error(f"Error in enhance_query: {e}")
            return user_query  # Return original query if enhancement fails

    def advanced_analyze_contracts(self, contracts_key: str, user_query: str) -> list:
        try:
            contracts = json.loads(contracts_key)
            prompt = f"Analyze the relevance of the following contracts to this query: {user_query}\n\n"
            for contract in contracts[:10]:  # Limit to 10 contracts to avoid token limit
                prompt += f"Contract: {json.dumps(contract)}\n"
            prompt += "\nProvide a relevance score (0-100) and brief explanation for each contract."
            
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens_to_sample=1000
            )
            
            # Parse the response and add relevance scores to contracts
            analyzed_contracts = []
            for contract, analysis in zip(contracts, response.completion.strip().split("\n\n")):
                try:
                    score = float(analysis.split(":")[1].split()[0])
                    explanation = ":".join(analysis.split(":")[2:]).strip()
                    analyzed_contracts.append({**contract, "relevance_score": score, "explanation": explanation})
                except Exception as e:
                    logger.error(f"Error parsing contract analysis: {e}")
                    analyzed_contracts.append({**contract, "relevance_score": 0, "explanation": "Analysis failed"})
            
            return analyzed_contracts
        except Exception as e:
            logger.error(f"Error in advanced_analyze_contracts: {e}")
            return contracts  # Return original contracts if analysis fails

    def summarize_results(self, result_key: str) -> str:
        try:
            results = json.loads(result_key)
            prompt = "Summarize the following government contract search results:\n\n"
            for result in results[:5]:  # Summarize top 5 results
                prompt += f"Title: {result.get('title', 'N/A')}\n"
                prompt += f"Agency: {result.get('agency', 'N/A')}\n"
                prompt += f"Relevance: {result.get('relevance_score', 'N/A')}\n\n"
            prompt += "Summary:"
            
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens_to_sample=200
            )
            return response.completion.strip()
        except Exception as e:
            logger.error(f"Error in summarize_results: {e}")
            return "Unable to generate summary due to an error."

    def extract_entities(self, contracts_key: str) -> dict:
        try:
            contracts = json.loads(contracts_key)
            prompt = "Extract key entities from the following government contracts. Focus on Organizations, Locations, Technologies, Key Personnel, and Important Dates.\n\n"
            for contract in contracts[:5]:  # Limit to 5 contracts
                prompt += f"Contract: {json.dumps(contract)}\n\n"
            prompt += "Extracted Entities:"
            
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens_to_sample=500
            )
            
            # Parse the response into a structured format
            entities = {
                "Organizations": [],
                "Locations": [],
                "Technologies": [],
                "Key Personnel": [],
                "Important Dates": []
            }
            current_category = None
            for line in response.completion.strip().split("\n"):
                line = line.strip()
                if line in entities:
                    current_category = line
                elif current_category and line:
                    entities[current_category].append(line)
            
            return entities
        except Exception as e:
            logger.error(f"Error in extract_entities: {e}")
            return {}  # Return empty dict if extraction fails
