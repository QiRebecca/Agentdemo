from scientific_agent_from_scratch.kernel import AgentKernel


def test_kernel_boot(tmp_path):
    kernel = AgentKernel(base_dir=tmp_path)
    assert "run_calculation" in {tool["name"] for tool in kernel.tool_registry.list_tools()}
    assert "report_writing" in {skill["name"] for skill in kernel.skill_registry.list()}
    state = kernel.create_state("demo goal", tmp_path / "run")
    assert state.goal == "demo goal"
    assert state.status == "initialized"
