
# Unset all supported CI's
unexport GCOVR_TEST_SUITE
export GCOVR_TEST_SUITE_NO_GIT_COMMAND := 1

unexport TRAVIS_JOB_ID
unexport APPVEYOR_URL
unexport JENKINS_URL
unexport GITHUB_ACTIONS
unexport GITHUB_HEAD_REF

all:
	$(CXX) -fprofile-arcs -ftest-coverage -fPIC main.cpp -o testcase

run: coveralls

coveralls: coveralls.stub.json coveralls.travis.json coveralls.appveyor.json coveralls.jenkins.json coveralls.github-actions.json coveralls.github-actions-pr.json
	# Pass

coverage.json:
	./testcase
	$(GCOVR) -d --json-pretty --json -o $@

coveralls.stub.json: export GCOVR_TEST_SUITE := 1
coveralls.stub.json: coverage.json
	$(GCOVR) --add-tracefile $< --coveralls-pretty --coveralls $@

coveralls.travis.json: export TRAVIS_JOB_ID := TRAVIS_JOB_ID
coveralls.travis.json: export TRAVIS_BUILD_NUMBER := TRAVIS_BUILD_NUMBER
coveralls.travis.json: export TRAVIS_PULL_REQUEST := 123
coveralls.travis.json: export TRAVIS_BRANCH := test_branch
coveralls.travis.json: export TRAVIS_COMMIT := TRAVIS_COMMIT
coveralls.travis.json: coverage.json
	$(GCOVR) --add-tracefile $< --coveralls-pretty --coveralls $@

coveralls.appveyor.json: export APPVEYOR_URL := APPVEYOR_URL
coveralls.appveyor.json: export APPVEYOR_JOB_ID := APPVEYOR_JOB_ID
coveralls.appveyor.json: export APPVEYOR_JOB_NUMBER := APPVEYOR_JOB_NUMBER
coveralls.appveyor.json: export APPVEYOR_REPO_COMMIT := APPVEYOR_REPO_COMMIT
coveralls.appveyor.json: export APPVEYOR_PULL_REQUEST_NUMBER := 123
coveralls.appveyor.json: export APPVEYOR_REPO_BRANCH := test_branch
coveralls.appveyor.json: coverage.json
	$(GCOVR) --add-tracefile $< --coveralls-pretty --coveralls $@

coveralls.jenkins.json: export JENKINS_URL := JENKINS_URL
coveralls.jenkins.json: export JOB_NAME := JOB_NAME
coveralls.jenkins.json: export BUILD_ID := BUILD_ID
coveralls.jenkins.json: export GIT_COMMIT := GIT_COMMIT
coveralls.jenkins.json: export CHANGE_ID := 123
coveralls.jenkins.json: export BRANCH_NAME := test_branch
coveralls.jenkins.json: coverage.json
	$(GCOVR) --add-tracefile $< --coveralls-pretty --coveralls $@

coveralls.github-actions.json: export GITHUB_ACTIONS := GITHUB_ACTIONS
coveralls.github-actions.json: export GITHUB_WORKFLOW := GITHUB_WORKFLOW
coveralls.github-actions.json: export GITHUB_RUN_ID := GITHUB_RUN_ID
coveralls.github-actions.json: export GITHUB_SHA := GITHUB_SHA
coveralls.github-actions.json: export GITHUB_REF := refs/head/test_branch
coveralls.github-actions.json: coverage.json
	$(GCOVR) --add-tracefile $< --coveralls-pretty --coveralls $@

coveralls.github-actions-pr.json: export GITHUB_ACTIONS := GITHUB_ACTIONS
coveralls.github-actions-pr.json: export GITHUB_WORKFLOW := GITHUB_WORKFLOW
coveralls.github-actions-pr.json: export GITHUB_RUN_ID := GITHUB_RUN_ID
coveralls.github-actions-pr.json: export GITHUB_SHA := GITHUB_SHA
coveralls.github-actions-pr.json: export GITHUB_HEAD_REF := refs/pull/123/merge
coveralls.github-actions-pr.json: export GITHUB_REF := test_branch
coveralls.github-actions-pr.json: coverage.json
	$(GCOVR) --add-tracefile $< --coveralls-pretty --coveralls $@

clean:
	rm -f testcase
	rm -f *.gc*
	rm -f coverage*.* coveralls.*.json
