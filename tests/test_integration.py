import sys
import os
from unittest.mock import MagicMock, patch

# Ensure we can import from src
sys.path.append(os.path.join(os.getcwd(), 'src'))

def test_slm_integration():
    print("Testing SLM Integration...")
    
    # Mocking SLMValidator to avoid loading the real model during tests
    with patch('hooks.main.SLMValidator') as MockValidator:
        instance = MockValidator.return_value
        instance.validate_candidate.return_value = True
        
        from hooks.main import slm_validation
        
        candidates = ["sk-proj-test123456789"]
        results = slm_validation(candidates)
        
        print(f"Results: {results}")
        
        # Verify that the validator was instantiated and called
        MockValidator.assert_called_once()
        instance.validate_candidate.assert_called_with(candidates[0])
        
        assert results[0][1] is True
        print("Integration logic verified (Mocked SLM).")

if __name__ == "__main__":
    try:
        test_slm_integration()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
