"""
条件边
"""
from typing import TypedDict, Literal

from langgraph.constants import START, END
from langgraph.graph import StateGraph


# 状态
class MyState(TypedDict):
    count: int
    maxCount: int


# 节点
def a(state: MyState):
    print(state["count"])
    return state


def b(state: MyState):
    state["count"] += 1
    return state

def b_1(state: MyState):
    state["count"] += 1
    return state


def c(state: MyState):
    print("c")
    state["count"] *= 2
    return state

def d(state: MyState):
    state["count"] += 1
    return state


# 路由函数
def route_condition(state: MyState) -> Literal["b", "end"]:
    if state["count"] < state["maxCount"]:
        return "b"
    else:
        return "end"


# 构建图
def compile():
    graph = StateGraph(MyState)
    graph.add_node("a", a)
    graph.add_node("b", b)
    graph.add_node("b_1", b_1)
    graph.add_node("c", c)
    graph.add_node("d", d)

    graph.add_edge(START, "a")
    graph.add_edge("a","b")
    graph.add_edge("a","c")
    graph.add_edge("b","b_1")
    graph.add_edge("b_1","d")
    graph.add_edge("c","d")
    graph.add_edge("d","end")

    graph.add_edge(["b_1", "c"], "d")


    return graph.compile()


if __name__ == "__main__":
    app = compile()
    result = app.invoke(input={
        "count": 2,
        "maxCount": 10,
    },
        config={
            "recursion_limit": 20
        })
    print(result)
