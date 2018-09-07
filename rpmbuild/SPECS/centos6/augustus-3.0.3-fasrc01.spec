#------------------- package info ----------------------------------------------

#
# enter the simple app name, e.g. myapp
#
Name: %{getenv:NAME}

#
# enter the app version, e.g. 0.0.1
#
Version: %{getenv:VERSION}

#
# enter the release; start with fasrc01 (or some other convention for your 
# organization) and increment in subsequent releases
#
# the actual "Release", %%{release_full}, is constructed dynamically; for Comp 
# and MPI apps, it will include the name/version/release of the apps used to 
# build it and will therefore be very long
#
%define release_short %{getenv:RELEASE}

#
# enter your FIRST LAST <EMAIL>
#
Packager: %{getenv:FASRCSW_AUTHOR}

#
# enter a succinct one-line summary (%%{summary} gets changed when the debuginfo 
# rpm gets created, so this stores it separately for later re-use); do not 
# surround this string with quotes
#
%define summary_static ...FIXME...
Summary: %{summary_static}

#
# enter the url from where you got the source; change the archive suffix if 
# applicable
#
URL: http://...FIXME...
Source: %{name}-%{version}.tar.gz

#
# there should be no need to change the following
#

#these fields are required by RPM
Group: fasrcsw
License: see COPYING file or upstream packaging

#this comes here since it uses Name and Version but dynamically computes Release, Prefix, etc.
%include fasrcsw_defines.rpmmacros

Release: %{release_full}
Prefix: %{_prefix}


#
# enter a description, often a paragraph; unless you prefix lines with spaces, 
# rpm will format it, so no need to worry about the wrapping
#
%description
...FIXME...



#------------------- %%prep (~ tar xvf) ---------------------------------------

%prep


#
# FIXME
#
# unpack the sources here.  The default below is for standard, GNU-toolchain 
# style things -- hopefully it'll just work as-is.
#

umask 022
cd "$FASRCSW_DEV"/rpmbuild/BUILD 
rm -rf %{name}-%{version}
tar xvf "$FASRCSW_DEV"/rpmbuild/SOURCES/%{name}-%{version}.tar.*
cd %{name}-%{version}
chmod -Rf a+rX,u+w,g-w,o-w .



#------------------- %%build (~ configure && make) ----------------------------

%build

#(leave this here)
%include fasrcsw_module_loads.rpmmacros


#
# FIXME
#
# configure and make the software here.  The default below is for standard 
# GNU-toolchain style things -- hopefully it'll just work as-is.
# 

##prerequisite apps (uncomment and tweak if necessary).  If you add any here, 
##make sure to add them to modulefile.lua below, too!
#module load NAME/VERSION-RELEASE
module load boost/1.55.0-fasrc01
module load zlib/1.2.8-fasrc02
#module load mysql++/3.2.1-fasrc01
#module load gsl/1.16-fasrc02
module load bamtools/2.3.0-fasrc01
module load samtools/0.1.19-fasrc01
module load htslib/1.1-fasrc01
module load bcftools/1.0-fasrc01
module load tabix/0.2.6-fasrc01

umask 022
cd "$FASRCSW_DEV"/rpmbuild/BUILD/%{name}-%{version}

# Clean up the object files
find auxprogs -name "*.o" | xargs rm -f
rm auxprogs/checkTargetSortedness/checkTargetSortedness
rm bin/*

# Update variables in auxprogs Makefiles
sed -i -e 's?^BAMTOOLS.*?BAMTOOLS = $(BAMTOOLS_HOME)?' \
        -e 's?^INCLUDES.*?INCLUDES = $(BAMTOOLS_INCLUDE)/bamtools?' \
        -e 's?libbamtools.a?bamtools/libbamtools.a?' auxprogs/bam2hints/Makefile
sed -i -e 's?^SAMTOOLS.*?SAMTOOLS = $(SAMTOOLS_INCLUDE)?' \
        -e 's?\(^CFLAGS.*\)?\1 -L$(ZLIB_LIB)?' auxprogs/checkTargetSortedness/Makefile
sed -i  -e 's?^SAMTOOLS.*?SAMTOOLS = $(SAMTOOLS_INCLUDE)?' \
        -e 's?^BCFTOOLS.*?BCFTOOLS = $(BCFTOOLS_HOME)?' \
        -e 's?^TABIX.*?TABIX = $(TABIX_INCLUDE)?' \
        -e 's?^HTSLIB.*?HTSLIB = $(HTSLIB_LIB)?' \
        -e 's?\(^CFLAGS.*\)?\1 -L$(ZLIB_LIB)?' auxprogs/bam2wig/Makefile

sed -i  -e 's?^INCLUDES.*?INCLUDES = -I$(BAMTOOLS_HOME)/include/bamtools -Iheaders -I$(BAMTOOLS_HOME)/src/toolkit?' \
        -e 's?^LIBS.*?LIBS = -L$(ZLIB_LIB) $(BAMTOOLS_HOME)/lib/bamtools/libbamtools.a -lz?' auxprogs/filterBam/src/Makefile
sed -i -e 's?^# ZIPINPUT?ZIPINPUT?' common.mk
       
make -j 4
(cd auxprogs/checkTargetSortedness && make)
(cd auxprogs/bam2hints && make)
(cd auxprogs/bam2wig && make)
export BAMTOOLS=$BAMTOOLS_HOME
(cd auxprogs/filterBam && make)


#------------------- %%install (~ make install + create modulefile) -----------

%install

#(leave this here)
%include fasrcsw_module_loads.rpmmacros


#
# FIXME
#
# make install here.  The default below is for standard GNU-toolchain style 
# things -- hopefully it'll just work as-is.
#
# Note that DESTDIR != %{prefix} -- this is not the final installation.  
# Rpmbuild does a temporary installation in the %{buildroot} and then 
# constructs an rpm out of those files.  See the following hack if your app 
# does not support this:
#
# https://github.com/fasrc/fasrcsw/blob/master/doc/FAQ.md#how-do-i-handle-apps-that-insist-on-writing-directly-to-the-production-location
#
# %%{buildroot} is usually ~/rpmbuild/BUILDROOT/%{name}-%{version}-%{release}.%{arch}.
# (A spec file cannot change it, thus it is not inside $FASRCSW_DEV.)
#

umask 022
cd "$FASRCSW_DEV"/rpmbuild/BUILD/%{name}-%{version}
echo %{buildroot} | grep -q %{name}-%{version} && rm -rf %{buildroot}
mkdir -p %{buildroot}/%{_prefix}
cp -a config bin scripts %{buildroot}%{_prefix}
cp auxprogs/bam2hints/bam2hints auxprogs/bam2wig/bam2wig auxprogs/checkTargetSortedness/checkTargetSortedness auxprogs/filterBam/bin/filterBam  %{buildroot}%{_prefix}/bin

#(this should not need to be changed)
#these files are nice to have; %%doc is not as prefix-friendly as I would like
#if there are other files not installed by make install, add them here
for f in COPYING AUTHORS README INSTALL ChangeLog NEWS THANKS TODO BUGS; do
	test -e "$f" && ! test -e '%{buildroot}/%{_prefix}/'"$f" && cp -a "$f" '%{buildroot}/%{_prefix}/'
done

#(this should not need to be changed)
#this is the part that allows for inspecting the build output without fully creating the rpm
%if %{defined trial}
	set +x
	
	echo
	echo
	echo "*************** fasrcsw -- STOPPING due to %%define trial yes ******************"
	echo 
	echo "Look at the tree output below to decide how to finish off the spec file.  (\`Bad"
	echo "exit status' is expected in this case, it's just a way to stop NOW.)"
	echo
	echo
	
	tree '%{buildroot}/%{_prefix}'

	echo
	echo
	echo "Some suggestions of what to use in the modulefile:"
	echo
	echo

	generate_setup.sh --action echo --format lmod --prefix '%%{_prefix}'  '%{buildroot}/%{_prefix}'

	echo
	echo
	echo "******************************************************************************"
	echo
	echo
	
	#make the build stop
	false

	set -x
%endif

# 
# FIXME (but the above is enough for a "trial" build)
#
# This is the part that builds the modulefile.  However, stop now and run 
# `make trial'.  The output from that will suggest what to add below.
#
# - uncomment any applicable prepend_path things (`--' is a comment in lua)
#
# - do any other customizing of the module, e.g. load dependencies -- make sure 
#   any dependency loading is in sync with the %%build section above!
#
# - in the help message, link to website docs rather than write anything 
#   lengthy here
#
# references on writing modules:
#   http://www.tacc.utexas.edu/tacc-projects/lmod/advanced-user-guide/writing-module-files
#   http://www.tacc.utexas.edu/tacc-projects/lmod/system-administrator-guide/initial-setup-of-modules
#   http://www.tacc.utexas.edu/tacc-projects/lmod/system-administrator-guide/module-commands-tutorial
#

mkdir -p %{buildroot}/%{_prefix}
cat > %{buildroot}/%{_prefix}/modulefile.lua <<EOF
local helpstr = [[
%{name}-%{version}-%{release_short}
%{summary_static}
]]
help(helpstr,"\n")

whatis("Name: %{name}")
whatis("Version: %{version}-%{release_short}")
whatis("Description: %{summary_static}")

---- prerequisite apps (uncomment and tweak if necessary)
if mode()=="load" then
	if not isloaded("boost/1.55.0-fasrc01") then
		load("boost/1.55.0-fasrc01")
	end
	if not isloaded("gsl") then
		load("gsl/1.16-fasrc02")
	end
	if not isloaded("mysql++") then
		load("mysql++/3.2.1-fasrc01")
	end
	if not isloaded("zlib") then
		load("zlib/1.2.8-fasrc02")
	end
end

---- environment changes (uncomment what's relevant)
prepend_path("PATH",                "%{_prefix}/bin")
prepend_path("PATH",                "%{_prefix}/scripts")
EOF



#------------------- %%files (there should be no need to change this ) --------

%files

%defattr(-,root,root,-)

%{_prefix}/*



#------------------- scripts (there should be no need to change these) --------


%pre
#
# everything in fasrcsw is installed in an app hierarchy in which some 
# components may need creating, but no single rpm should own them, since parts 
# are shared; only do this if it looks like an app-specific prefix is indeed 
# being used (that's the fasrcsw default)
#
echo '%{_prefix}' | grep -q '%{name}.%{version}' && mkdir -p '%{_prefix}'
#

%post
#
# symlink to the modulefile installed along with the app; we want all rpms to 
# be relocatable, hence why this is not a proper %%file; as with the app itself, 
# modulefiles are in an app hierarchy in which some components may need 
# creating
#
mkdir -p %{modulefile_dir}
ln -s %{_prefix}/modulefile.lua %{modulefile}
#


%preun
#
# undo the module file symlink done in the %%post; do not rmdir 
# %%{modulefile_dir}, though, since that is shared by multiple apps (yes, 
# orphans will be left over after the last package in the app family 
# is removed)
#
test -L '%{modulefile}' && rm '%{modulefile}'
#

%postun
#
# undo the last component of the mkdir done in the %%pre (yes, orphans will be 
# left over after the last package in the app family is removed); also put a 
# little protection so this does not cause problems if a non-default prefix 
# (e.g. one shared with other packages) is used
#
test -d '%{_prefix}' && echo '%{_prefix}' | grep -q '%{name}.%{version}' && rmdir '%{_prefix}'
#


%clean
#
# wipe out the buildroot, but put some protection to make sure it isn't 
# accidentally / or something -- we always have "rpmbuild" in the name
#
echo '%{buildroot}' | grep -q 'rpmbuild' && rm -rf '%{buildroot}'
#
