"""
Comprehensive test suite for AskIAM-Assistant backend components.
Tests for SQL validation, entity validation, error detection, and validation pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from mcp.validators import _is_error_result


# ======================== SQL VALIDATION TOOL TESTS ========================

class TestValidateSQLTool:
    """Test SQL validation tool (validate_sql_tool)."""
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_valid_simple_select(self, mock_tracer):
        """Test valid simple SELECT statement."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'SELECT * FROM Users',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_insert_keyword(self, mock_tracer):
        """Test INSERT keyword rejection."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_sql_tool.invoke({
                'sql': 'INSERT INTO Users VALUES (1)',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_update_keyword(self, mock_tracer):
        """Test UPDATE keyword rejection."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_sql_tool.invoke({
                'sql': 'UPDATE Users SET name = "test"',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_delete_keyword(self, mock_tracer):
        """Test DELETE keyword rejection."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Only SELECT"):
            validate_sql_tool.invoke({
                'sql': 'DELETE FROM Users',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_union_keyword(self, mock_tracer):
        """Test UNION keyword rejection."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Forbidden SQL keyword"):
            validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users UNION SELECT * FROM Roles',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_join_keyword(self, mock_tracer):
        """Test JOIN keyword rejection."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Forbidden SQL keyword"):
            validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users JOIN Roles',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_non_select(self, mock_tracer):
        """Test rejection of non-SELECT queries."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Only SELECT statements"):
            validate_sql_tool.invoke({
                'sql': 'DESCRIBE Users',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_multiple_statements(self, mock_tracer):
        """Test rejection of multiple statements."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Multiple SQL statements"):
            validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users; DROP TABLE Users',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_missing_from_clause(self, mock_tracer):
        """Test rejection of queries without FROM clause."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="FROM clause"):
            validate_sql_tool.invoke({
                'sql': 'SELECT 1',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_reject_unauthorized_table(self, mock_tracer):
        """Test rejection of unauthorized table."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        with pytest.raises(ValueError, match="Unauthorized table"):
            validate_sql_tool.invoke({
                'sql': 'SELECT * FROM UnauthorizedTable',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_whitespace_handling(self, mock_tracer):
        """Test handling of extra whitespace."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': '  SELECT  *  FROM  Users  ',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_newlines_in_sql(self, mock_tracer):
        """Test handling of newlines in SQL."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'SELECT *\nFROM Users\nWHERE id = 1',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_case_insensitive_keywords(self, mock_tracer):
        """Test case insensitivity of keywords."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'select * from Users',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_keyword_in_string_literal(self, mock_tracer):
        """Test keywords inside string literals are allowed."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        # Note: The validator doesn't distinguish between keywords in literals vs keywords
        # This test documents current behavior - delete keyword still triggers rejection
        with pytest.raises(ValueError, match="Forbidden SQL keyword"):
            validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users WHERE name = "DELETE"',
                'allowed_table': 'Users'
            })
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_select_with_limit(self, mock_tracer):
        """Test SELECT with LIMIT clause."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'SELECT id, name FROM Users LIMIT 10',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_select_with_where_clause(self, mock_tracer):
        """Test SELECT with WHERE clause."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'SELECT * FROM Users WHERE id = 1',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_select_with_order_by(self, mock_tracer):
        """Test SELECT with ORDER BY clause."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'SELECT * FROM Users ORDER BY name ASC',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_select_with_aggregate(self, mock_tracer):
        """Test SELECT with aggregate functions."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'SELECT COUNT(*), MAX(id) FROM Users',
            'allowed_table': 'Users'
        })
        assert result == "ok"
    
    @patch('mcp.tools.sql_validator.get_tracer')
    def test_select_with_group_by(self, mock_tracer):
        """Test SELECT with GROUP BY clause."""
        from mcp.tools.sql_validator import validate_sql_tool
        mock_tracer.return_value.is_enabled.return_value = False
        
        result = validate_sql_tool.invoke({
            'sql': 'SELECT role, COUNT(*) FROM Users GROUP BY role',
            'allowed_table': 'Users'
        })
        assert result == "ok"


# ======================== ERROR DETECTION TESTS ========================

class TestErrorDetectionBasic:
    """Basic error detection tests."""
    
    def test_detect_error_keyword(self):
        """Test detection of ERROR keyword."""
        assert _is_error_result("ERROR: syntax error") is True
    
    def test_detect_unable_to_execute(self):
        """Test detection of 'unable to execute' message."""
        assert _is_error_result("unable to execute query") is True
    
    def test_detect_exception(self):
        """Test detection of exception."""
        assert _is_error_result("Exception occurred: invalid query") is True
    
    def test_detect_invalid(self):
        """Test detection of 'invalid' keyword."""
        assert _is_error_result("invalid SQL statement") is True
    
    def test_detect_failed(self):
        """Test detection of 'failed' keyword."""
        assert _is_error_result("Query failed to execute") is True
    
    def test_detect_does_not_exist(self):
        """Test detection of 'does not exist' message."""
        assert _is_error_result('relation "users" does not exist') is True
    
    def test_detect_sqlstate(self):
        """Test detection of SQLSTATE error codes."""
        assert _is_error_result('[SQLSTATE 42P01]') is True


class TestErrorDetectionValidResults:
    """Test valid result detection."""
    
    def test_ok_result(self):
        """Test OK result."""
        assert _is_error_result("OK") is False
    
    def test_valid_json_result(self):
        """Test valid JSON result."""
        assert _is_error_result('{"status": "success", "data": []}') is False
    
    def test_empty_result(self):
        """Test empty result."""
        assert _is_error_result("") is False
    
    def test_null_result(self):
        """Test null result."""
        assert _is_error_result(None) is False
    
    def test_success_message(self):
        """Test success message."""
        assert _is_error_result("Query executed successfully") is False


class TestErrorDetectionEdgeCases:
    """Test edge cases in error detection."""
    
    def test_case_insensitive_detection(self):
        """Test case insensitive error detection."""
        assert _is_error_result("error: syntax error") is True
    
    def test_none_input(self):
        """Test handling of None input."""
        assert _is_error_result(None) is False
    
    def test_non_string_input(self):
        """Test handling of non-string input."""
        assert _is_error_result(123) is False
    
    def test_very_long_error_message(self):
        """Test handling of very long error message."""
        result = _is_error_result("ERROR: " + "x" * 10000)
        assert result is True
    
    def test_postgresql_specific_errors(self):
        """Test PostgreSQL specific error messages."""
        errors = [
            'ERROR: permission denied for relation "users"',
            'ERROR: duplicate key value violates unique constraint',
            'ERROR: foreign key violation'
        ]
        for error in errors:
            assert _is_error_result(error) is True
    
    def test_general_database_errors(self):
        """Test general database error messages."""
        errors = [
            'ERROR: database connection failed',
            'ERROR: query timeout',
            'ERROR: connection refused'
        ]
        for error in errors:
            assert _is_error_result(error) is True
    
    def test_list_input(self):
        """Test handling of list input."""
        assert _is_error_result([]) is False
    
    def test_dict_input(self):
        """Test handling of dict input."""
        assert _is_error_result({}) is False


# ======================== ENTITY VALIDATION TESTS ========================

class TestEntityValidationTool:
    """Test entity validation tool."""
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_empty_value_rejection(self, mock_validate, mock_generate):
        """Test rejection of empty values."""
        from mcp.tools.entity_validator import validate_entity_tool
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': ''
        })
        assert "Error" in result
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_none_value_rejection(self, mock_validate, mock_generate):
        """Test rejection of None values."""
        from mcp.tools.entity_validator import validate_entity_tool
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': None
        })
        assert "Error" in result


# ======================== VALIDATION WORKFLOW TESTS ========================

class TestValidationErrorHandling:
    """Test error handling in validation."""
    
    def test_is_error_result_with_string(self):
        """Test _is_error_result with string inputs."""
        assert _is_error_result("ERROR: something") is True
        assert _is_error_result("Normal result") is False
    
    def test_is_error_result_type_handling(self):
        """Test _is_error_result type handling."""
        # Non-string should return False
        assert _is_error_result(42) is False
        assert _is_error_result(True) is False
        assert _is_error_result(None) is False
    
    def test_is_error_result_case_insensitivity(self):
        """Test case insensitive error detection."""
        assert _is_error_result("error: database error") is True
        assert _is_error_result("ERROR: database error") is True
        assert _is_error_result("Error: database error") is True
    
    def test_is_error_result_multiple_indicators(self):
        """Test detection with multiple error indicators."""
        assert _is_error_result("unable to execute: invalid query") is True
        assert _is_error_result("exception failed") is True

# ======================== BOUNDARY AND CORNER CASE TESTS ========================

class TestBoundaryConditions:
    """Test boundary conditions and corner cases."""
    
    def test_zero_length_string_error_detection(self):
        """Test empty string for error detection."""
        assert _is_error_result("") is False
    
    def test_single_character_error(self):
        """Test single character strings."""
        assert _is_error_result("E") is False
        assert _is_error_result("e") is False
    
    def test_error_as_substring_in_larger_word(self):
        """Test error as substring in larger word."""
        # "terror" contains "error" but should still match
        assert _is_error_result("terror") is True
    
    def test_case_variations_of_error_indicators(self):
        """Test all case variations."""
        assert _is_error_result("ERROR") is True
        assert _is_error_result("Error") is True
        assert _is_error_result("error") is True
        assert _is_error_result("eRrOr") is True
    
    def test_error_with_leading_zeros(self):
        """Test error message with leading zeros."""
        assert _is_error_result("ERROR: 000001") is True
    
    def test_error_with_only_numbers(self):
        """Test whether pure numbers are errors."""
        assert _is_error_result("0000") is False
        assert _is_error_result("12345") is False
    
    def test_error_with_only_special_characters(self):
        """Test error with only special characters."""
        assert _is_error_result("!@#$%^&*") is False
        assert _is_error_result("ERROR: !@#$%") is True
    
    def test_very_long_valid_result(self):
        """Test very long non-error result."""
        long_result = "x" * 1000000  # 1MB string
        assert _is_error_result(long_result) is False
    
    def test_result_with_null_bytes(self):
        """Test result with null bytes."""
        result = "ERROR\x00message"
        assert _is_error_result(result) is True
    
    def test_result_with_control_characters(self):
        """Test result with control characters."""
        result = "ERROR\x01\x02\x03"
        assert _is_error_result(result) is True
    
    def test_float_value(self):
        """Test float value."""
        assert _is_error_result(3.14) is False
    
    def test_boolean_true(self):
        """Test boolean True."""
        assert _is_error_result(True) is False
    
    def test_boolean_false(self):
        """Test boolean False."""
        assert _is_error_result(False) is False
    
    def test_empty_list(self):
        """Test empty list."""
        assert _is_error_result([]) is False
    
    def test_empty_dict(self):
        """Test empty dict."""
        assert _is_error_result({}) is False
    
    def test_list_with_error_string(self):
        """Test list containing error string."""
        assert _is_error_result(["ERROR"]) is False
    
    def test_dict_with_error_key(self):
        """Test dict with error key."""
        assert _is_error_result({"ERROR": "value"}) is False


class TestSQLValidationBoundaryConditions:
    """Test SQL validation boundary conditions."""
    
    def test_select_with_zero_offset(self):
        """Test SELECT with OFFSET 0."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users LIMIT 10 OFFSET 0',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_select_with_huge_limit(self):
        """Test SELECT with huge LIMIT."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users LIMIT 999999999',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_select_column_named_from(self):
        """Test column named 'from'."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT "from" FROM Users',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_select_column_named_select(self):
        """Test column named 'select'."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT "select" FROM Users',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_numeric_literals(self):
        """Test numeric literals in WHERE clause."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users WHERE id = 0 OR id = -1 OR id = 999',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_float_literals(self):
        """Test float literals in WHERE clause."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users WHERE salary > 1000.50',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_boolean_literals(self):
        """Test boolean literals."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users WHERE active = true OR active = false',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_complex_boolean_expression(self):
        """Test complex boolean expressions."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users WHERE (a AND b) OR (c AND d) OR (e AND f)',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_deeply_nested_parentheses(self):
        """Test deeply nested parentheses."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            result = validate_sql_tool.invoke({
                'sql': 'SELECT * FROM Users WHERE ((((((a = 1)))))) AND b = 2',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_many_columns_in_select(self):
        """Test SELECT with many columns."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            cols = ', '.join([f'col{i}' for i in range(1000)])
            result = validate_sql_tool.invoke({
                'sql': f'SELECT {cols} FROM Users',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_multiple_where_conditions(self):
        """Test multiple WHERE conditions."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            conditions = ' AND '.join([f'col{i} = {i}' for i in range(100)])
            result = validate_sql_tool.invoke({
                'sql': f'SELECT * FROM Users WHERE {conditions}',
                'allowed_table': 'Users'
            })
            assert result == "ok"
    
    def test_where_with_or_chains(self):
        """Test WHERE with chained OR conditions."""
        from mcp.tools.sql_validator import validate_sql_tool
        with patch('mcp.tools.sql_validator.get_tracer') as mock_tracer:
            mock_tracer.return_value.is_enabled.return_value = False
            
            conditions = ' OR '.join([f'status = "status{i}"' for i in range(50)])
            result = validate_sql_tool.invoke({
                'sql': f'SELECT * FROM Users WHERE {conditions}',
                'allowed_table': 'Users'
            })
            assert result == "ok"


class TestErrorDetectionBoundaryConditions:
    """Test error detection boundary conditions."""
    
    def test_single_char_indicators(self):
        """Test single character indicator patterns."""
        # These should not match
        assert _is_error_result("e") is False
        assert _is_error_result("u") is False
        assert _is_error_result("i") is False
    
    def test_truncated_error_words(self):
        """Test truncated error indicator words."""
        assert _is_error_result("err") is False
        assert _is_error_result("fail") is False
        assert _is_error_result("inval") is False
    
    def test_error_indicators_separated_by_space(self):
        """Test error indicators separated by space."""
        assert _is_error_result("E R R O R") is False
        assert _is_error_result("invalid") is True
    
    def test_error_with_leading_spaces(self):
        """Test error with leading spaces."""
        assert _is_error_result("   ERROR: message") is True
    
    def test_error_with_trailing_spaces(self):
        """Test error with trailing spaces."""
        assert _is_error_result("ERROR: message   ") is True
    
    def test_error_surrounded_by_special_chars(self):
        """Test error surrounded by special characters."""
        assert _is_error_result("***ERROR***") is True
        assert _is_error_result(">>>ERROR<<<") is True


class TestEntityValidationBoundaryConditions:
    """Test entity validation boundary conditions."""
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_single_character_value(self, mock_validate, mock_generate):
        """Test single character value."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE name = "a"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': 'a'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_numeric_string_value(self, mock_validate, mock_generate):
        """Test numeric string value."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE name = "0"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': '0'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_negative_number_as_string(self, mock_validate, mock_generate):
        """Test negative number as string."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE name = "-123"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': '-123'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_scientific_notation_string(self, mock_validate, mock_generate):
        """Test scientific notation string."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE name = "1.23e-4"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': '1.23e-4'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_boolean_string_values(self, mock_validate, mock_generate):
        """Test boolean string values."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE name = "true"'
        
        for val in ['true', 'false', 'True', 'False', 'TRUE', 'FALSE']:
            result = validate_entity_tool.invoke({
                'table': 'Users',
                'id_column': 'user_id',
                'name_column': 'name',
                'value': val
            })
            assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_date_format_string(self, mock_validate, mock_generate):
        """Test date format string."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE name = "2024-01-28T12:30:45"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': '2024-01-28T12:30:45'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_uuid_format_string(self, mock_validate, mock_generate):
        """Test UUID format string."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE name = "550e8400-e29b-41d4-a716-446655440000"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'name',
            'value': '550e8400-e29b-41d4-a716-446655440000'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_email_format_string(self, mock_validate, mock_generate):
        """Test email format string."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE email = "user+tag@example.co.uk"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'email',
            'value': 'user+tag@example.co.uk'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_ip_address_format(self, mock_validate, mock_generate):
        """Test IP address format."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE ip = "192.168.1.1"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'ip',
            'value': '192.168.1.1'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_ipv6_address_format(self, mock_validate, mock_generate):
        """Test IPv6 address format."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'ipv6',
            'value': '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_phone_number_format(self, mock_validate, mock_generate):
        """Test phone number format."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE phone = "+1-555-123-4567"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'phone',
            'value': '+1-555-123-4567'
        })
        assert result is not None
    
    @patch('mcp.tools.entity_validator.generate_sql_tool')
    @patch('mcp.tools.entity_validator.validate_sql_tool')
    def test_credit_card_format(self, mock_validate, mock_generate):
        """Test credit card format."""
        from mcp.tools.entity_validator import validate_entity_tool
        mock_generate.invoke.return_value = 'SELECT user_id FROM Users WHERE card = "4532-1488-0343-6467"'
        
        result = validate_entity_tool.invoke({
            'table': 'Users',
            'id_column': 'user_id',
            'name_column': 'card',
            'value': '4532-1488-0343-6467'
        })
        assert result is not None


class TestValidationTypeConversions:
    """Test type conversions and coercions."""
    
    def test_string_boolean_conversion(self):
        """Test string vs boolean."""
        assert _is_error_result("true") is False
        assert _is_error_result("false") is False
    
    def test_numeric_string_edge_cases(self):
        """Test numeric strings."""
        assert _is_error_result("0") is False
        assert _is_error_result("1") is False
        assert _is_error_result("-1") is False
    
    def test_zero_vs_none(self):
        """Test zero vs None."""
        assert _is_error_result(0) is False
        assert _is_error_result(None) is False
    
    def test_empty_vs_none(self):
        """Test empty string vs None."""
        assert _is_error_result("") is False
        assert _is_error_result(None) is False


class TestConcurrentScenarios:
    """Test scenarios involving multiple sequential operations."""
    
    def test_alternating_errors_and_valid_results(self):
        """Test alternating errors and valid results."""
        results = [
            _is_error_result("ERROR: 1"),
            _is_error_result("Valid result 1"),
            _is_error_result("ERROR: 2"),
            _is_error_result("Valid result 2"),
        ]
        assert results == [True, False, True, False]
    
    def test_mixed_error_indicators(self):
        """Test mixed error indicators in sequence."""
        errors = [
            "ERROR: test",
            "unable to execute",
            "invalid query",
            "failed operation",
            "does not exist",
            "exception occurred"
        ]
        assert all(_is_error_result(e) is True for e in errors)
    
    def test_mixed_valid_results(self):
        """Test mixed valid results in sequence."""
        valid = [
            "OK",
            "Success",
            '{"status": "ok"}',
            "[]",
            "1 row returned",
            "Completed successfully"
        ]
        assert all(_is_error_result(v) is False for v in valid)