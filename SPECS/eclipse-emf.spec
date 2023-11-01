%global _eclipsedir %{_prefix}/lib/eclipse

%global emf_tag R2_22_0
%global xsd_tag R2_22_0

# Set this flag to avoid building everything except for the core bundles
# Allows building into a brand new buildroot before Eclipse is even built
%bcond_with bootstrap

Epoch:     1
Name:      eclipse-emf
Version:   2.22.0
Release:   1%{?dist}
Summary:   EMF and XSD Eclipse plug-ins

License:   EPL-2.0
URL:       https://www.eclipse.org/modeling/emf/
Source0:   https://git.eclipse.org/c/emf/org.eclipse.emf.git/snapshot/org.eclipse.emf-%{emf_tag}.tar.xz
Source1:   https://git.eclipse.org/c/xsd/org.eclipse.xsd.git/snapshot/org.eclipse.xsd-%{xsd_tag}.tar.xz

# Avoid hard build-time dep on nebula (not in Fedora)
Patch0:    0001-Remove-dependency-on-nebula.patch
# Remove test that requires internet connection
Patch1:    0002-Remove-test-that-requires-talking-to-the-internet.patch

BuildRequires: tycho
BuildRequires: tycho-extras
%if %{without bootstrap}
BuildRequires: eclipse-pde
%endif

BuildArch: noarch

# Upstream Eclipse no longer supports non-64bit arches
ExclusiveArch: x86_64

%description
The Eclipse Modeling Framework (EMF) and XML Schema Definition (XSD) plug-ins.

%package   core
Summary:   Eclipse EMF Core Bundles

%description core
Core EMF bundles required by the Eclipse platform.

%if %{without bootstrap}

%package   runtime
Summary:   Eclipse Modeling Framework (EMF) Eclipse plug-in

%description runtime
The Eclipse Modeling Framework (EMF) allows developers to build tools and
other applications based on a structured data model. From a model
specification described in XMI, EMF provides tools and run-time support to
produce a set of Java classes for the model, along with a set of adapter
classes that enable viewing and command-based editing of the model, and a
basic editor.

%package   xsd
Summary:   XML Schema Definition (XSD) Eclipse plug-in
# Obsoletes added in F28
Obsoletes: eclipse-xsd < %{version}-%{release}
Provides:  eclipse-xsd = %{version}-%{release}

%description xsd
The XML Schema Definition (XSD) plug-in is a library that provides an API for
manipulating the components of an XML Schema as described by the W3C XML
Schema specifications, as well as an API for manipulating the DOM-accessible
representation of XML Schema as a series of XML documents.

%package   sdk
Summary:   Eclipse EMF and XSD SDK
# Obsoletes added in F28
Obsoletes: %{name}-tests < %{version}-%{release}
Obsoletes: %{name}-examples < %{version}-%{release}
Obsoletes: eclipse-xsd-examples < %{version}-%{release}
Obsoletes: eclipse-xsd-sdk < %{version}-%{release}
Provides:  eclipse-xsd-sdk = %{version}-%{release}

%description sdk
Documentation and developer resources for the Eclipse Modeling Framework
(EMF) plug-in and XML Schema Definition (XSD) plug-in.
%endif

%prep
%setup -c -T -q -a 0 -a 1
mv org.eclipse.emf-%{emf_tag}/ org.eclipse.emf/
mv org.eclipse.xsd-%{xsd_tag}/ org.eclipse.xsd/

%patch0 -p1
%patch1 -p1

pushd org.eclipse.emf

# TODO: ODA, GWT, Xtext and RAP components are not packaged, so don't build corresponding bundles
sed -i -e '/org.eclipse.emf.gwt/d' releng/org.eclipse.emf.parent/{plugins,features}/pom.xml
sed -i -e '/org.eclipse.emf.oda/d' releng/org.eclipse.emf.parent/{plugins,features}/pom.xml
sed -i -e '/org.eclipse.emf.rap/d' releng/org.eclipse.emf.parent/{plugins,features}/pom.xml
sed -i -e '/codegen.ecore.xtext/d' releng/org.eclipse.emf.parent/{plugins,features}/pom.xml
sed -i -e '/ecore.xcore/d' releng/org.eclipse.emf.parent/{plugins,features}/pom.xml
sed -i -e '/test.edit.ui.rap/d' releng/org.eclipse.emf.parent/{plugins,features}/pom.xml
%pom_xpath_remove "plugin[@id='org.eclipse.emf.test.edit.ui.rap']" tests/org.eclipse.emf.tests-feature/feature.xml

# Disable example bundles, we don't want to ship them
%pom_disable_module "../../../examples/org.eclipse.emf.examples-feature" releng/org.eclipse.emf.parent/features
%pom_disable_module "../../../../org.eclipse.xsd/features/org.eclipse.xsd.example-feature" releng/org.eclipse.emf.parent/features
sed -i -e '/<module>.*examples/d' releng/org.eclipse.emf.parent/plugins/pom.xml
%pom_xpath_remove "plugin[@id='org.eclipse.emf.test.examples']" tests/org.eclipse.emf.tests-feature/feature.xml

# Disable modules unneeded for tycho build
%pom_disable_module "tp" releng/org.eclipse.emf.parent
%pom_disable_module "../org.eclipse.emf.site" releng/org.eclipse.emf.parent
%pom_disable_module '../../../features/org.eclipse.emf.all-feature' releng/org.eclipse.emf.parent/features

# Disable jgit/target platform stuff that we can't use in RPM builds
%pom_remove_plugin :target-platform-configuration releng/org.eclipse.emf.parent
%pom_remove_dep :tycho-sourceref-jgit releng/org.eclipse.emf.parent
%pom_remove_dep :tycho-buildtimestamp-jgit releng/org.eclipse.emf.parent
%pom_xpath_remove 'pom:configuration/pom:timestampProvider' releng/org.eclipse.emf.parent
%pom_xpath_remove 'pom:configuration/pom:jgit.ignore' releng/org.eclipse.emf.parent
%pom_xpath_remove 'pom:configuration/pom:jgit.dirtyWorkingTree' releng/org.eclipse.emf.parent
%pom_xpath_remove 'pom:configuration/pom:sourceReferences' releng/org.eclipse.emf.parent

%if %{with bootstrap}
# Only build core modules when bootstrapping
%pom_xpath_replace "pom:modules" "<modules>
<module>../../../features/org.eclipse.emf.base-feature</module>
<module>../../../features/org.eclipse.emf.license-feature</module>
<module>../../../features/org.eclipse.emf.common-feature</module>
<module>../../../features/org.eclipse.emf.ecore-feature</module>
</modules>" releng/org.eclipse.emf.parent/features
%pom_xpath_replace "pom:modules" "<modules>
<module>../../../plugins/org.eclipse.emf.common</module>
<module>../../../plugins/org.eclipse.emf.ecore.change</module>
<module>../../../plugins/org.eclipse.emf.ecore.xmi</module>
<module>../../../plugins/org.eclipse.emf.ecore</module>
</modules>" releng/org.eclipse.emf.parent/plugins
%endif

popd

# Don't install poms or license features
%mvn_package "::pom::" __noinstall
%mvn_package ":org.eclipse.{emf,xsd}.license" __noinstall
%mvn_package ":org.eclipse.emf.base" __noinstall

# No need to ship tests as they are run at buildtime
%mvn_package ":org.eclipse.emf.tests" __noinstall
%mvn_package ":org.eclipse.emf.test.*" __noinstall

%if %{with bootstrap}
%mvn_package ":::{sources,sources-feature}:" __noinstall
%else
%mvn_package ":::{sources,sources-feature}:" sdk
%endif
%mvn_package ":org.eclipse.emf.{sdk,doc,cheatsheets,example.installer}" sdk
%mvn_package ":org.eclipse.xsd.{sdk,doc,cheatsheets,example.installer}" sdk
%mvn_package "org.eclipse.emf.features:org.eclipse.emf.{base,common,ecore}"
%mvn_package "org.eclipse.emf:org.eclipse.emf.{common,ecore,ecore.change,ecore.xmi}"
%mvn_package ":org.eclipse.xsd*" xsd
%mvn_package ":org.eclipse.emf.mapping.xsd**" xsd
%mvn_package ":" runtime

%build
# Qualifier generated from last modification time of source tarball
QUALIFIER=$(date -u -d"$(stat --format=%y %{SOURCE0})" +v%Y%m%d-%H%M)
%mvn_build -j -- -f org.eclipse.emf/pom.xml -DforceContextQualifier=$QUALIFIER -Dmaven.test.failure.ignore=true

%install
%mvn_install

# Move to libdir due to being part of core platform
install -d -m 755 %{buildroot}%{_eclipsedir}
mv %{buildroot}%{_datadir}/eclipse/droplets/emf/{plugins,features} %{buildroot}%{_eclipsedir}
rm -r %{buildroot}%{_datadir}/eclipse/droplets/emf

# Fixup metadata
sed -i -e 's|%{_datadir}/eclipse/droplets/emf|%{_eclipsedir}|' %{buildroot}%{_datadir}/maven-metadata/eclipse-emf.xml
sed -i -e 's|%{_datadir}/eclipse/droplets/emf/features/|%{_eclipsedir}/features/|' \
       -e 's|%{_datadir}/eclipse/droplets/emf/plugins/|%{_eclipsedir}/plugins/|' .mfiles
sed -i -e '/droplets/d' .mfiles

# Remove any symlinks that might be created during bootstrapping due to missing platform bundles
for del in $( (cd %{buildroot}%{_eclipsedir}/plugins && ls | grep -v -e '^org\.eclipse\.emf' ) ) ; do
rm %{buildroot}%{_eclipsedir}/plugins/$del
sed -i -e "/$del/d" .mfiles
done

%files core -f .mfiles
%license org.eclipse.emf/features/org.eclipse.emf.license-feature/*.html

%if %{without bootstrap}

%files runtime -f .mfiles-runtime

%files xsd -f .mfiles-xsd

%files sdk -f .mfiles-sdk
%endif

%changelog
* Thu Jun 18 2020 Mat Booth <mat.booth@redhat.com> - 1:2.22.0-1
- Update to latest upstream release

* Fri Mar 20 2020 Mat Booth <mat.booth@redhat.com> - 1:2.21.0-1
- Update to latest upstream release

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1:2.20.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Tue Jan 14 2020 Mat Booth <mat.booth@redhat.com> - 1:2.20.0-4
- Use Epoch for all subpackages to avoid repo sanity check failures

* Thu Dec 19 2019 Mat Booth <mat.booth@redhat.com> - 2.20.0-3
- Full build

* Wed Dec 18 2019 Mat Booth <mat.booth@redhat.com> - 2.20.0-2
- Enable bootstrap mode

* Wed Dec 18 2019 Mat Booth <mat.booth@redhat.com> - 2.20.0-1
- Update to latest upstream release

* Fri Sep 13 2019 Mat Booth <mat.booth@redhat.com> - 2.19.0-1
- Update to latest upstream release
- Don't ship base feature

* Sat Jun 15 2019 Mat Booth <mat.booth@redhat.com> - 2.18.0-1
- Update to latest upstream release

* Wed May 08 2019 Mat Booth <mat.booth@redhat.com> - 2.16.0-3
- Restrict to same architectures as Eclipse itself

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 2.16.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Dec 04 2018 Mat Booth <mat.booth@redhat.com> - 2.16.0-1
- Update to 2018-12 release

* Mon Aug 20 2018 Mat Booth <mat.booth@redhat.com> - 2.15.0-0.3.gitd1e5fdd
- Non-bootstrap build

* Sun Aug 19 2018 Mat Booth <mat.booth@redhat.com> - 2.15.0-0.2.gitd1e5fdd
- Fix bootstrap build mode

* Fri Aug 17 2018 Mat Booth <mat.booth@redhat.com> - 2.15.0-0.1.gitd1e5fdd
- License correction and update to latest snapshot

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.14.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed May 09 2018 Mat Booth <mat.booth@redhat.com> - 2.14.0-1
- Update to Photon release
- Add XSD sub-package (in line with upstream's new combined tycho build)
- Run tests during maven build, no longer any need to package them
- Also drop examples sub-package

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.13.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.13.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jun 15 2017 Mat Booth <mat.booth@redhat.com> - 2.13.0-2
- Allow conditionally building tests
- Add a bootstrap mode for building in new buildroots

* Thu Jun 15 2017 Mat Booth <mat.booth@redhat.com> - 2.13.0-1
- Update to Oxygen release

* Tue May 16 2017 Mat Booth <mat.booth@redhat.com> - 2.13.0-0.1.git72f1720
- Update to latest Oxygen snapshot

* Thu Apr 06 2017 Mat Booth <mat.booth@redhat.com> - 2.12.0-5
- Make package noarch now that Eclipse is in the same location on all arches
- Drop old obsoletes/provides

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.12.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 07 2016 Mat Booth <mat.booth@redhat.com> - 2.12.0-3
- Re-add XSD dep

* Mon Nov 07 2016 Mat Booth <mat.booth@redhat.com> - 2.12.0-2
- Set qualifiers to source-modification-time instead of build-time, to eliminate
  descrepancies between architectures
- Temporarily remove dep on XSD

* Mon Jun 13 2016 Mat Booth <mat.booth@redhat.com> - 2.12.0-1
- Update to Neon release

* Tue May 10 2016 Mat Booth <mat.booth@redhat.com> - 2.12.0-0.1.git2021583
- Update to latest Neon snapshot

* Sat Feb 27 2016 Mat Booth <mat.booth@redhat.com> - 2.11.2-1
- Update to Mars.2 release

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.11.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Sep 28 2015 Mat Booth <mat.booth@redhat.com> - 2.11.1-1
- Update to Mars.1 release
- Build with maven/tycho
- Add tests package

* Mon Jun 29 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-4
- Remove incomplete SCL macros

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.11.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 02 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-2
- Revert moving bundles into core package

* Tue Jun 02 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-1
- Update to 2.11.0 release
- Move extra e4 tools deps into core package
- Switch to xz tarball

* Sat May 30 2015 Alexander Kurtakov <akurtako@redhat.com> 1:2.10.2-2
- Move emf.edit to core as it's required by e4 now.

* Wed Mar 04 2015 Mat Booth <mat.booth@redhat.com> - 2.10.2-1
- Update to Luna SR2 release

* Thu Nov 20 2014 Mat Booth <mat.booth@redhat.com> - 2.10.1-3
- Qualifier must be same on all arches in archful builds

* Wed Nov 19 2014 Mat Booth <mat.booth@redhat.com> - 2.10.1-2
- Make core package archful so it can be installed into libdir
  where eclipse-platform expects it to be
- Move eclipse-emf -> eclipse-emf-runtime, this is because we can have
  noarch sub-packages of an archful package, but cannot have archful
  sub-packages of a noarch package
- Fix some minor rpmlint errors

* Wed Oct 01 2014 Mat Booth <mat.booth@redhat.com> - 2.10.1-1
- Update to Luna SR1 release
- Drop ancient obsoletes on emf-sdo package

* Wed Jun 25 2014 Mat Booth <mat.booth@redhat.com> - 2.10.0-1
- Update to latest upstream release
- Fix obsoletes on emf-core package, rhbz #1095431
- Move edit plugin from core to main package

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Apr 17 2014 Mat Booth <mat.booth@redhat.com> - 2.9.2-2
- Drop XSD packages, these are now packaged separately
- Drop ancient obsolete of emf-standalone.

* Wed Mar 12 2014 Mat Booth <fedora@matbooth.co.uk> - 2.9.2-1
- Update to latest upstream, Kepler SR2
- Drop requires on java, rhbz #1068039
- Remove unused patch
- Update project URL

* Mon Sep 30 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.1-1
- Update to latest upstream.  

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Jun 21 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.0-1
- Update to Kepler release.

* Fri Jun 21 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.0-0.2.git352e28
- 974108: Remove versions and timestamps from EMF filenames.

* Wed May 1 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.0-0.1.git352e28
- Update to latest upstream.

* Thu Mar 21 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-20
- Initial SCLization.

* Mon Jan 28 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-7
- Really fix RHBZ#894154.

* Thu Jan 17 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-6
- Move emf.edit back to eclipse-emf-core and symlink it.

* Thu Jan 17 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-5
- Fix for RHBZ#894154

* Mon Dec 17 2012 Alexander Kurtakov <akurtako@redhat.com> 1:2.8.1-4
- Remove unneeded things.

* Mon Oct 8 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-3
- Avoid generating automatic OSGi dependencies (yet another attempt).

* Mon Oct 8 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-2
- Avoid generating automatic OSGi dependencies. (fix)

* Mon Oct 1 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-1
- Update to upstream 2.8.1 release

* Wed Sep 12 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-17
- Avoid generating automatic OSGi dependencies.

* Wed Aug 15 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-16
- Removed obsolete.

* Tue Aug 14 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-15
- Moved Obs emf-core to emf-core package.
- Removed dropins symlinks.

* Tue Aug 14 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-14
- Added Epoch to eclipse-emf-core.
- Updated eclipse-pde dependency version to 4.2.0.

* Mon Aug 13 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-13
- Move emf.edit to eclipse-emf-core.

* Fri Aug 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-12
- Lower eclipse-platform version requirement (CBI Eclipse is not in yet).

* Fri Aug 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-11
- Get rid off conflicts clause.

* Thu Aug 2 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-10
- Moving core back to emf package (for CBI build).

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jul 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-1
- Update to upstream Juno.

* Mon May 7 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.7.e674bb28ad412fc9bc786f2f9b3c157eb2cbdae0
- Update to M7.

* Mon Apr 16 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.6.postM6
- Bugs 812870, 812872 - fix building index for documentation.

* Tue Apr 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.5.postM6
- Remove %%clean section.
- Remove duplicated plugins.

* Mon Apr 2 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.4.postM6
- Use %%{bindir}/eclipse-pdebuild.

* Thu Mar 29 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.3.postM6
- Back noarch.
- Use the eclipse-emf-core from main eclipse-emf.

* Thu Mar 29 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.2.postM6
- Removed the noarch tag.

* Thu Mar 29 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.1.postM6
- Update to latest upstream version.
- Package eclipse-emf-core created for the need of Eclipse 4.2. 
- Removed usage of Eclipse reconciler script.

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 29 2011 Jeff Johnston <jjohnstn@redhat.com> 2.7.1-1
- Update to 2.7.1.
- Add rhel flags.

* Wed Oct 5 2011 Sami Wagiaalla <swagiaal@redhat.com> 2.7.0-2
- Use the reconciler to install/uninstall plugins during rpm
  post and postun respectively.

* Thu Sep 15 2011 Roland Grunberg <rgrunber@redhat.com> 2.7.0-1
- Update to 2.7.0.
- Re-apply necessary patches, content-handler error fixed upstream.
- licenses now exist in org.eclipse.{emf,xsd}.license-feature only.

* Wed Sep 14 2011 Roland Grunberg <rgrunber@redhat.com> 2.6.1-2
- Fix RHBZ #716165 using old patches.
- Fix ContentHandler casting issue.

* Fri Mar 18 2011 Mat Booth <fedora@matbooth.co.uk> 2.6.1-1
- Update to 2.6.1.

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jul 19 2010 Charley Wang <chwang@redhat.com> - 2.6.0-1
- Update to 2.6.0

* Sat Sep 19 2009 Mat Booth <fedora@matbooth.co.uk> - 2.5.0-4
- Re-enable jar repacking now that RHBZ #461854 has been resolved.

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul 02 2009 Mat Booth <fedora@matbooth.co.uk> 2.5.0-2
- SDK requires PDE for example plug-in projects.

* Sun Jun 28 2009 Mat Booth <fedora@matbooth.co.uk> 2.5.0-1
- Update to 2.5.0 final release (Galileo).
- Build the features seperately to allow for a saner %%files section.

* Fri May 22 2009 Alexander Kurtakov <akurtako@redhat.com> 2.5.0-0.2.RC1
- Update to 2.5.0 RC1.
- Use %%global instead of %%define. 

* Sat Apr 18 2009 Mat Booth <fedora@matbooth.co.uk> 2.5.0-0.1.M6
- Update to Milestone 6 release of 2.5.0.
- Require Eclipse 3.5.0.

* Tue Apr 7 2009 Alexander Kurtakov <akurtako@redhat.com> 2.4.2-3
- Fix directory ownership.

* Mon Mar 23 2009 Alexander Kurtakov <akurtako@redhat.com> 2.4.2-2
- Rebuild to not ship p2 context.xml.
- Remove context.xml from %%files section.

* Sat Feb 28 2009 Mat Booth <fedora@matbooth.co.uk> 2.4.2-1
- Update for Ganymede SR2.

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Feb 03 2009 Mat Booth <fedora@matbooth.co.uk> 2.4.1-4
- Make context qualifier the same as upstream.

* Sat Jan 10 2009 Mat Booth <fedora@matbooth.co.uk> 2.4.1-3
- Removed AOT bits and change package names to what they used to be.
- Obsolete standalone package.

* Tue Dec 23 2008 Mat Booth <fedora@matbooth.co.uk> 2.4.1-2
- Build example installer plugins using the source from the tarball instead of
  trying to get the examples from source control a second time.

* Fri Dec 12 2008 Mat Booth <fedora@matbooth.co.uk> 2.4.1-1
- Initial release, based on eclipse-gef spec file, but with disabled AOT
  compiled bits because of RHBZ #477707.