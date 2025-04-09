import pytest 
from unittest.mock import patch, MagicMock, AsyncMock

from src.tools.project import project_file_list
from src.tools.story_details import get_story_details
from src.tools.get_analysis_messages import get_analysis_conversation
from src.tools.file_parser import parse_files


# #####
# ## This file contains mock tests for the functions I implemented to be used as tools by the StoryAgent. simply run pytest -vs test_util_functions.py in the test directory

# #####




# #####
# ## Start of test cases for project_file_list function
# #####

@pytest.mark.asyncio
@patch('src.tools.project.supabase')
async def test_project_file_list_success(mock_supabase):
    #setup chain of methods
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    #setup chain of calls
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq

    # Create sample data for the test
    sample_files = {
        "data": [
            {
                "id": "file1",
                "display_name": "Test File 1",
                "file_url": "https://example.com/file1",
                "extension": "pdf",
                "tags": ["tag1", "tag2"],
                "project_id": "project_123",
                "index_status": "complete"
            }
        ]
    }

    # set the return value for executing the query
    mock_eq.execute.return_value = MagicMock(**sample_files)


    # Call the actual function with a test project id
    test_project_id = "project_123"
    result = await project_file_list(test_project_id)

    #Make some assertions
    mock_supabase.table.assert_called_once_with("files")

    mock_table.select.assert_called_once_with(
        "id", "display_name", "file_url", "extension",
        "tags", "index_status"
    )

    mock_select.eq.assert_called_once_with("project_id", test_project_id)

    assert result == sample_files["data"]


@pytest.mark.asyncio
@patch('src.tools.project.supabase')
async def test_project_file_list_empty(mock_supabase):
    #setup chain of methods
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()

    #setup chain of calls
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq

    sample_files = {
        "data": []
    }

    #setup the return value for query execution
    mock_eq.execute.return_value = MagicMock(**sample_files)

    #Call the actual function with a test project_id
    test_project_id = "project_123"
    result = await project_file_list(test_project_id)

    #Make some assertions
    mock_supabase.table.assert_called_once_with("files")
    mock_table.select.assert_called_once_with(
        "id", "display_name", "file_url", "extension",
        "tags", "index_status"
    )
    mock_select.eq.assert_called_once_with("project_id", test_project_id)

    assert result == []


@pytest.mark.asyncio
@patch('src.tools.project.supabase')
async def test_project_file_list_error(mock_supabase):
    #setup method calls
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    

    #setup chain of calls
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq

    # Set up the exception with a specific message
    mock_eq.execute.side_effect = Exception("Supabase query failed")
    

    # Call the function and capture the exception
    test_project_id = "project_123"
    try:
        await project_file_list(test_project_id)
        pytest.fail("\nExpected an exception but none was raised")
    except Exception as e:
        
        print(f"\nCaught exception: {e}")
        print(f"Exception type: {type(e)}")

        # verify it's the right exception
        assert str(e) == "Supabase query failed"
    
    #assertions
    mock_supabase.table.assert_called_once_with("files")
    mock_table.select.assert_called_once_with(
        "id", "display_name", "file_url", "extension",
        "tags", "index_status"
    )
    mock_select.eq.assert_called_once_with("project_id", test_project_id)
    mock_eq.execute.assert_called_once()

# ## End of test cases for project_file_list function


# #####
# ## Start of test cases for get_story_details function
# #####

@pytest.mark.asyncio
@patch("src.tools.story_details.supabase")
async def test_get_story_details_success(mock_supabase):
    #setup method calls
    mock_table = MagicMock()
    mock_select =  MagicMock()
    mock_eq = MagicMock()

    #setup chain of calls
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq

    sample_data = {
        "data": [{"id": "134dfg45", "projectId": "ab56nh67jks2"}]
    }

    #setup the return value for the query
    mock_eq.execute.return_value = MagicMock(**sample_data)

    #Call the actual function
    test_story_id = "story_1234"
    result = await get_story_details(test_story_id)

    #make assertions
    mock_supabase.table.assert_called_once_with("stories")
    mock_table.select.assert_called_once_with("id", "projectId")
    mock_select.eq.assert_called_once_with("id", test_story_id)

    assert result == sample_data["data"]

@pytest.mark.asyncio
@patch("src.tools.story_details.supabase")
async def test_get_story_details_error(mock_supabase):
    #setup method calls
    mock_table = MagicMock()
    mock_select =  MagicMock()
    mock_eq = MagicMock()

    #setup chain of calls
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.side_effect = Exception("Query failed")

    try:
        test_story_id = "story_1234"
        await get_story_details(test_story_id)
        pytest.fail("\nExpected an exception but none was raised")
    
    except Exception as e:
        print(f"\n Caught an exception: {e}")
        print(f"\n Exception type: {type(e)}")

    #make assertions
    mock_supabase.table.assert_called_once_with("stories")
    mock_table.select.assert_called_once_with("id", "projectId")
    mock_select.eq.assert_called_once_with("id", test_story_id)

# ## End of test cases for get_story_details function


# #####
# ## Start of test cases for get_analysis_conversation function
# #####

@pytest.mark.asyncio
@patch("src.tools.get_analysis_messages.supabase")
async def test_get_analysis_conversation_success(mock_supabase):
    #setup method calls
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_order = MagicMock()
    

    #setup of chain of calls
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.order.return_value = mock_order

    sample_data = {
        "data":[
            {
            "id": "1",
            "role": "user",
            "content": "analyse the news pdf file"
        },
        {
            "id": "2",
            "role": "assistant",
            "content": "I am starting the analysis"
        },
        {
            "id": "3",
            "role": "assistant",
            "content": "Here are some interesting findings"
        },
        ]
        }
    
    mock_order.execute.return_value = MagicMock(**sample_data)

    test_analysis_id = "analysis_1234"
    result = await get_analysis_conversation(test_analysis_id)

    #make assertions
    mock_supabase.table.assert_called_once_with("analysis_messages")
    mock_table.select.assert_called_once_with("*")
    mock_select.eq.assert_called_once_with("id", test_analysis_id)
    mock_eq.order.assert_called_once_with("created_at", desc=True)

    assert result == sample_data["data"]

@pytest.mark.asyncio
@patch("src.tools.get_analysis_messages.supabase")
async def test_get_analysis_conversation_error(mock_supabase):
    #setup method calls
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_order = MagicMock()
    

    #setup of chain of calls
    mock_supabase.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.order.return_value = mock_order

    
    
    mock_order.execute.side_effect = Exception("Query failed")

    try:
        test_analysis_id = "analysis_1234"
        await get_analysis_conversation(test_analysis_id)
        pytest.fail("\nExpected an exception but none was raised")
    
    except Exception as e:
        print(f"\n Caught an exception: {e}")
        print(f"\n Exception type: {type(e)}")

    #make assertions
    mock_supabase.table.assert_called_once_with("analysis_messages")
    mock_table.select.assert_called_once_with("*")
    mock_select.eq.assert_called_once_with("id", test_analysis_id)
    mock_eq.order.assert_called_once_with("created_at", desc=True)

# ## End of test cases for get_analysis_conversation function


# #####
# ## Start of test cases for parse_files function
# #####

@pytest.mark.asyncio
@patch("src.tools.file_parser.LlamaParse")
async def test_parse_files_success(mock_llama_parse_class):

    #Create a mock instance of LlamaParse
    mock_parser = MagicMock()
    
    mock_llama_parse_class.return_value = mock_parser 

    #Create mock documents
    mock_doc_1 = MagicMock()
    mock_doc_2 = MagicMock()
    mock_doc_3 = MagicMock()

    mock_doc_1.text = "The report revealed .."
    mock_doc_2.text = "The agency has embezzled state funds"
    mock_doc_3.text = "Crime unit has confiscated some items during the investigation"

    #Setup the aload_data method  of LlamaParse to return mock documents
    mock_parser.aload_data = AsyncMock(return_value=[mock_doc_1, mock_doc_2, mock_doc_3])

    #Call the actual function
    test_file_url = "https://storage.example.com/news.pdf"
    result = await parse_files(test_file_url)

    #make assertions
    
    mock_parser.aload_data.assert_called_once_with(
        file_path= test_file_url
    )

    expected_result = "The report revealed ..\n\nThe agency has embezzled state funds\n\nCrime unit has confiscated some items during the investigation"
    assert result == expected_result

@pytest.mark.asyncio
@patch("src.tools.file_parser.LlamaParse")
async def test_parse_files_error(mock_llama_parse_class):
    #Create mock instance of LlamaParse class
    mock_parser = MagicMock()
    mock_llama_parse_class.return_value = mock_parser

    #setup the return value of aload_data
    mock_parser.aload_data = AsyncMock(side_effect=Exception("Failed to parse file"))

    try:
        test_file_url = "https://storage.example.com/news.pdf"
        await parse_files(test_file_url)
        pytest.fail("\nExpected an exception but none was raised")
        
    except Exception as e:
        print(f"\n Caught an exception: {e}")
        assert "Failed to parse file" in str(e)

    #make assertions
    
    mock_parser.aload_data.assert_called_once_with(
        file_path= test_file_url
    )

# ## End of test cases for parse_files function