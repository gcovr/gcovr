
clean:
	- for dir in `ls -d *`; do\
	  if [ -d "$${dir}" ] && [ -e "$${dir}/Makefile" ]; then\
	     cd $${dir};\
	     make -f Makefile clean;\
	     cd ..;\
	  fi;\
	done
