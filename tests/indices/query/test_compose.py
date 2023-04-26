"""Test composing indices."""

from typing import Any, Dict, List
from unittest.mock import patch

from gpt_index.indices.composability.graph import ComposableGraph
from gpt_index.indices.keyword_table.simple_base import GPTSimpleKeywordTableIndex
from gpt_index.indices.list.base import GPTListIndex
from gpt_index.indices.tree.base import GPTTreeIndex
from gpt_index.langchain_helpers.chain_wrapper import (
    LLMChain,
    LLMMetadata,
    LLMPredictor,
)
from gpt_index.langchain_helpers.text_splitter import TokenTextSplitter
from gpt_index.readers.schema.base import Document
from tests.mock_utils.mock_predict import (
    mock_llmchain_predict,
    mock_llmpredictor_predict,
)
from tests.mock_utils.mock_prompts import (
    MOCK_QUERY_PROMPT,
    MOCK_REFINE_PROMPT,
    MOCK_TEXT_QA_PROMPT,
)
from tests.mock_utils.mock_text_splitter import mock_token_splitter_newline


@patch.object(TokenTextSplitter, "split_text", side_effect=mock_token_splitter_newline)
@patch.object(LLMPredictor, "predict", side_effect=mock_llmpredictor_predict)
@patch.object(LLMPredictor, "total_tokens_used", return_value=0)
@patch.object(LLMPredictor, "__init__", return_value=None)
def test_recursive_query_list_tree(
    _mock_init: Any,
    _mock_total_tokens_used: Any,
    _mock_predict: Any,
    _mock_split_text: Any,
    documents: List[Document],
    index_kwargs: Dict,
) -> None:
    """Test query."""
    list_kwargs = index_kwargs["list"]
    tree_kwargs = index_kwargs["tree"]
    # try building a list for every two, then a tree
    list1 = GPTListIndex.from_documents(documents[0:2], **list_kwargs)
    list2 = GPTListIndex.from_documents(documents[2:4], **list_kwargs)
    list3 = GPTListIndex.from_documents(documents[4:6], **list_kwargs)
    list4 = GPTListIndex.from_documents(documents[6:8], **list_kwargs)

    summary1 = "summary1"
    summary2 = "summary2"
    summary3 = "summary3"
    summary4 = "summary4"
    summaries = [summary1, summary2, summary3, summary4]

    # there are two root nodes in this tree: one containing [list1, list2]
    # and the other containing [list3, list4]
    graph = ComposableGraph.from_indices(
        GPTTreeIndex,
        [
            list1,
            list2,
            list3,
            list4,
        ],
        index_summaries=summaries,
        **tree_kwargs
    )
    assert isinstance(graph, ComposableGraph)
    query_str = "What is?"
    # query should first pick the left root node, then pick list1
    # within list1, it should go through the first document and second document
    query_engine = graph.as_query_engine()
    response = query_engine.query(query_str)
    assert str(response) == (
        "What is?:What is?:This is a test v2.:This is another test."
    )


@patch.object(TokenTextSplitter, "split_text", side_effect=mock_token_splitter_newline)
@patch.object(LLMPredictor, "predict", side_effect=mock_llmpredictor_predict)
@patch.object(LLMPredictor, "total_tokens_used", return_value=0)
@patch.object(LLMPredictor, "__init__", return_value=None)
def test_recursive_query_tree_list(
    _mock_init: Any,
    _mock_total_tokens_used: Any,
    _mock_predict: Any,
    _mock_split_text: Any,
    documents: List[Document],
    index_kwargs: Dict,
) -> None:
    """Test query."""
    list_kwargs = index_kwargs["list"]
    tree_kwargs = index_kwargs["tree"]
    # try building a tree for a group of 4, then a list
    # use a diff set of documents
    tree1 = GPTTreeIndex.from_documents(documents[2:6], **tree_kwargs)
    tree2 = GPTTreeIndex.from_documents(documents[:2] + documents[6:], **tree_kwargs)
    summaries = [
        "tree_summary1",
        "tree_summary2",
    ]

    # there are two root nodes in this tree: one containing [list1, list2]
    # and the other containing [list3, list4]
    graph = ComposableGraph.from_indices(
        GPTListIndex, [tree1, tree2], index_summaries=summaries, **list_kwargs
    )
    assert isinstance(graph, ComposableGraph)
    query_str = "What is?"
    # query should first pick the left root node, then pick list1
    # within list1, it should go through the first document and second document
    query_engine = graph.as_query_engine()
    response = query_engine.query(query_str)
    assert str(response) == (
        "What is?:What is?:This is a test.:What is?:This is a test v2."
    )


@patch.object(TokenTextSplitter, "split_text", side_effect=mock_token_splitter_newline)
@patch.object(LLMPredictor, "predict", side_effect=mock_llmpredictor_predict)
@patch.object(LLMPredictor, "total_tokens_used", return_value=0)
@patch.object(LLMPredictor, "__init__", return_value=None)
def test_recursive_query_table_list(
    _mock_init: Any,
    _mock_total_tokens_used: Any,
    _mock_predict: Any,
    _mock_split_text: Any,
    documents: List[Document],
    index_kwargs: Dict,
) -> None:
    """Test query."""
    list_kwargs = index_kwargs["list"]
    table_kwargs = index_kwargs["table"]
    # try building a tree for a group of 4, then a list
    # use a diff set of documents
    table1 = GPTSimpleKeywordTableIndex.from_documents(documents[4:6], **table_kwargs)
    table2 = GPTSimpleKeywordTableIndex.from_documents(documents[2:3], **table_kwargs)
    summaries = [
        "table_summary1",
        "table_summary2",
    ]

    graph = ComposableGraph.from_indices(
        GPTListIndex, [table1, table2], index_summaries=summaries, **list_kwargs
    )
    assert isinstance(graph, ComposableGraph)
    query_str = "World?"
    query_engine = graph.as_query_engine()
    response = query_engine.query(query_str)
    assert str(response) == ("World?:World?:Hello world.:None")

    query_str = "Test?"
    response = query_engine.query(query_str)
    assert str(response) == ("Test?:Test?:This is a test.:Test?:This is a test.")


@patch.object(TokenTextSplitter, "split_text", side_effect=mock_token_splitter_newline)
@patch.object(LLMPredictor, "predict", side_effect=mock_llmpredictor_predict)
@patch.object(LLMPredictor, "total_tokens_used", return_value=0)
@patch.object(LLMPredictor, "__init__", return_value=None)
def test_recursive_query_list_table(
    _mock_init: Any,
    _mock_total_tokens_used: Any,
    _mock_predict: Any,
    _mock_split_text: Any,
    documents: List[Document],
    index_kwargs: Dict,
) -> None:
    """Test query."""
    list_kwargs = index_kwargs["list"]
    table_kwargs = index_kwargs["table"]
    # try building a tree for a group of 4, then a list
    # use a diff set of documents
    # try building a list for every two, then a tree
    list1 = GPTListIndex.from_documents(documents[0:2], **list_kwargs)
    list2 = GPTListIndex.from_documents(documents[2:4], **list_kwargs)
    list3 = GPTListIndex.from_documents(documents[4:6], **list_kwargs)
    list4 = GPTListIndex.from_documents(documents[6:8], **list_kwargs)
    summaries = [
        "foo bar",
        "apple orange",
        "toronto london",
        "cat dog",
    ]

    graph = ComposableGraph.from_indices(
        GPTSimpleKeywordTableIndex,
        [list1, list2, list3, list4],
        index_summaries=summaries,
        **table_kwargs
    )
    assert isinstance(graph, ComposableGraph)
    query_str = "Foo?"
    query_engine = graph.as_query_engine()
    response = query_engine.query(query_str)
    assert str(response) == ("Foo?:Foo?:This is a test v2.:This is another test.")
    query_str = "Orange?"
    response = query_engine.query(query_str)
    assert str(response) == ("Orange?:Orange?:This is a test.:Hello world.")
    query_str = "Cat?"
    response = query_engine.query(query_str)
    assert str(response) == ("Cat?:Cat?:This is another test.:This is a test v2.")


@patch.object(LLMChain, "predict", side_effect=mock_llmchain_predict)
@patch("gpt_index.llm_predictor.base.OpenAI")
@patch.object(LLMPredictor, "get_llm_metadata", return_value=LLMMetadata())
@patch.object(LLMChain, "__init__", return_value=None)
def test_recursive_query_list_tree_token_count(
    _mock_init: Any,
    _mock_llm_metadata: Any,
    _mock_llmchain: Any,
    _mock_predict: Any,
    documents: List[Document],
    index_kwargs: Dict,
) -> None:
    """Test query."""
    list_kwargs = index_kwargs["list"]
    tree_kwargs = index_kwargs["tree"]
    # try building a list for every two, then a tree
    list1 = GPTListIndex.from_documents(documents[0:2], **list_kwargs)
    list2 = GPTListIndex.from_documents(documents[2:4], **list_kwargs)
    list3 = GPTListIndex.from_documents(documents[4:6], **list_kwargs)
    list4 = GPTListIndex.from_documents(documents[6:8], **list_kwargs)

    summary1 = "summary1"
    summary2 = "summary2"
    summary3 = "summary3"
    summary4 = "summary4"
    summaries = [summary1, summary2, summary3, summary4]

    # there are two root nodes in this tree: one containing [list1, list2]
    # and the other containing [list3, list4]
    # import pdb; pdb.set_trace()
    graph = ComposableGraph.from_indices(
        GPTTreeIndex,
        [
            list1,
            list2,
            list3,
            list4,
        ],
        index_summaries=summaries,
        **tree_kwargs
    )
    custom_retrievers = {
        graph.root_id: graph.root_index.as_retriever(
            query_template=MOCK_QUERY_PROMPT,
            text_qa_template=MOCK_TEXT_QA_PROMPT,
            refine_template=MOCK_REFINE_PROMPT,
        )
    }
    assert isinstance(graph, ComposableGraph)
    # first pass prompt is "summary1\nsummary2\n" (6 tokens),
    # response is the mock response (10 tokens)
    # total is 16 tokens, multiply by 2 to get the total
    assert graph.service_context.llm_predictor.total_tokens_used == 32

    query_str = "What is?"
    # query should first pick the left root node, then pick list1
    # within list1, it should go through the first document and second document
    start_token_ct = graph.service_context.llm_predictor.total_tokens_used
    query_engine = graph.as_query_engine(custom_retrievers=custom_retrievers)
    query_engine.query(query_str)
    # prompt is which is 35 tokens, plus 10 for the mock response
    assert graph.service_context.llm_predictor.total_tokens_used - start_token_ct == 45
