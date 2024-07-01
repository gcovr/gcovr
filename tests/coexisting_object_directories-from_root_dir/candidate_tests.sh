#!/usr/bin/env bash

# The script describes working and failing cases
# when having several coexisting build folders.

set -eu

root_dir="$(realpath "$(dirname "$0")")"

build () {
	cmake -G "Ninja" -DCMAKE_BUILD_TYPE=PROFILE -S ${root_dir} -B ${root_dir}/build/$1 -D ODD=$2
	cmake --build ${root_dir}/build/$1
}
#
# run coverage data
run () {
	${root_dir}/build/$1/parallel_call
}

# calling gcovr from project root dir
# specifying object dir and search dir
# coexisting_object_directories
generate_coverage_ok_1 () {
	gcovr \
		--gcov-executable /usr/bin/gcov \
		--object-directory ${root_dir}/build/$1 \
		--output ${root_dir}/coverage.$1.txt \
		${root_dir}/build/$1
}

# calling gcovr from project root dir
# specifying object dir
# not specifying search dir
# => object files from other build directories are processed.
# coexisting_object_directories_without_search_directory
generate_coverage_fail_11 () {
	gcovr \
		--gcov-executable /usr/bin/gcov \
		--object-directory ${root_dir}/build/$1 \
		--output ${root_dir}/coverage.$1.txt
}

# calling gcovr from project root dir
# not specifying object dir
# specifying search dir
# => race conditions when triggering several gcovr calls.
generate_coverage_fail_12 () {
	gcovr \
		--gcov-executable /usr/bin/gcov \
		--output ${root_dir}/coverage.$1.txt \
		${root_dir}/build/$1
}

# calling gcovr from project build dir
# specifying object dir
# specifying root dir
# specifying search dir
generate_coverage_ok_2 () {
	cd ${root_dir}/build/$1
	gcovr \
		--gcov-executable /usr/bin/gcov \
		--object-directory ${root_dir}/build/$1 \
		--output ${root_dir}/coverage.$1.txt \
		--root ${root_dir} \
		${root_dir}/build/$1
	cd -
}

# calling gcovr from project build dir
# specifying object dir
# specifying root dir
# not specifying search dir
# => object files from other build directories are processed.
generate_coverage_fail_21 () {
	cd ${root_dir}/build/$1
	gcovr \
		--gcov-executable /usr/bin/gcov \
		--object-directory ${root_dir}/build/$1 \
		--output ${root_dir}/coverage.$1.txt \
		--root ${root_dir}
	cd -
}

# calling gcovr from project build dir
# not specifying object dir
# specifying root dir
# specifying search dir
# => race conditions when triggering several gcovr calls.
generate_coverage_fail_22 () {
	cd ${root_dir}/build/$1
	gcovr \
		--gcov-executable /usr/bin/gcov \
		--output ${root_dir}/coverage.$1.txt \
		--root ${root_dir} \
		${root_dir}/build/$1
	cd -
}

compare () {
	set +e
	for v in a b c ; do diff \
		--brief \
		--ignore-matching-lines="^Directory:" \
		${root_dir}/reference/gcc-12/coverage.$v.txt \
		${root_dir}/coverage.$v.txt ; done
}

cd ${root_dir}
rm -f coverage.?.txt
rm -rf ${root_dir}/build

for v in a c ; do build $v ON; done
for v in b ; do build $v OFF; done
for v in a b c ; do run $v ; done

#for v in a b c ; do generate_coverage_ok_1 $v & done ; wait
#for v in a b c ; do generate_coverage_fail_11 $v : done # fails with incorrect reports
#for v in a b c ; do generate_coverage_fail_12 $v & done ; wait # fails with race conditions

#for v in a b c ; do generate_coverage_ok_2 $v ; done
#for v in a b c ; do generate_coverage_fail_21 $v ; done # fails with incorrect reports
#for v in a b c ; do generate_coverage_fail_22 $v & done ; wait # fails with race conditions

compare

