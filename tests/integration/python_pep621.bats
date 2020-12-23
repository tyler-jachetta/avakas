#!/usr/bin/env bats
# -*- mode: Shell-script;bash -*-

load helper


setup() {
	shared_setup
	REPO_ORIGIN=$(fake_repo)
	origin_repo "$REPO_ORIGIN"
	REPO=$(clone_repo $REPO_ORIGIN)
}

teardown() {
	shared_teardown
}

test_show(){
    SKELETON="$1"

    template_skeleton "${REPO_ORIGIN}" "${SKELETON}" "0.0.1"
    avakas_wrapper show "${REPO}"
    scan_lines "0.0.1" "${lines[@]}"
}

test_bump() {
    # There probably shouldn't be any difference between major/minor/patch
    # bumps with current implementation, but probably good to test for the
    # future in case implementation changes.
    SKELETON="$1"

    # patch 

    template_skeleton "${REPO_ORIGIN}" "${SKELETON}" "0.0.1"
    avakas_wrapper set "${REPO}" "0.0.2"
    avakas_wrapper show "${REPO}"
    scan_lines "0.0.2" "${lines[@]}"

    # Minor
    avakas_wrapper set "${REPO}" "0.1.0"
    avakas_wrapper show "${REPO}"
    scan_lines "0.1.0" "${lines[@]}"

    # Major
    avakas_wrapper set "${REPO}" "3.0.0"
    avakas_wrapper show "${REPO}"
    scan_lines "3.0.0" "${lines[@]}"

}

@test "set a package version" {
    avakas_wrapper set "$REPO" "0.0.2"
    scan_lines "Version set to 0.0.2" "${lines[@]}"
    avakas_wrapper show "$REPO"
    scan_lines "0.0.2" "${lines[@]}"
    [ -e "$REPO/version" ]
}

@test "bump a package version" {
    avakas_wrapper bump "$REPO" patch
    scan_lines "Version updated from 0.0.1 to 0.0.2" "${lines[@]}"
    avakas_wrapper show "$REPO"
    scan_lines "0.0.2" "${lines[@]}"
    [ -e "$REPO/version" ]
}

@test "Ensure that vanilla PEP 621 will not apply when other sub-flavors are applied" {
    # This is implicitly covered in other tests, but I feel that it is probably
    # wise to do thsi -TMJ
    template_skeleton "pyproject.toml/poetry.toml"
    
}

@test "show vanilla PEP 621 package version" {
    test_show "pyproject.toml/vanilla.toml"
}

@test "show poetry package version" {
    test_show "pyproject.toml/poetry.toml" 
}

@test "show setuptools package version" {
    test_show "pyproject.toml/setuptools.toml"
}

@test "set Vanilla PEP 621 package version" {
    test_bump "pyproject.toml/vanilla.toml"
}

@test "set Poetry PEP 621 package version" {
    test_bump "pyproject.toml/poetry.toml"
}

@test "set PEP 621 package version using Setuptools" {
    test_bump "pyproject.toml/setuptools.toml"
}