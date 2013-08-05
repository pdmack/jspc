%global namedreltag  -alpha-3
%global namedversion %{version}%{?namedreltag}
%global dotreltag    %(echo %{namedreltag} | tr - .)

Name:          jspc
Version:       2.0
Release:       0.6%{dotreltag}%{?dist}
Summary:       Compile JSPs under Maven
Group:         Development/Libraries
License:       ASL 2.0
Url:           http://mojo.codehaus.org/jspc/
# svn export https://svn.codehaus.org/mojo/tags/jspc-2.0-alpha-3 jspc
# tar czf jspc-2.0-alpha-3-src-svn.tar.gz jspc
Source0:       %{name}-%{namedversion}-src-svn.tar.gz
Source1:       %{name}-mp-plugin.xml
Patch0:        %{name}-ant-groovyc.patch

BuildRequires: java-devel
# TODO: migrate to xmvn beyond F18
BuildRequires: maven-local

BuildRequires: apache-resource-bundles
BuildRequires: ant
BuildRequires: fusesource-pom
BuildRequires: mvn(commons-lang:commons-lang)
BuildRequires: mvn(org.apache.maven.shared:file-management)
BuildRequires: plexus-container-default
BuildRequires: tomcat

BuildRequires: maven-enforcer-plugin
BuildRequires: maven-invoker-plugin
BuildRequires: maven-plugin-cobertura
BuildRequires: maven-plugin-plugin
BuildRequires: maven-remote-resources-plugin
BuildRequires: maven-install-plugin

Requires:      java
BuildArch:     noarch

%description
The Codehaus is a collaborative environment for building open source
projects with a strong emphasis on modern languages, focused on
quality components that meet real world needs.

Provides support to precompile your JSPs and have them included into
your WAR file. Version 2 of the JSP compilation support includes a
pluggable JSP compiler implementation, which currently allows different
versions of the Tomcat Jasper compiler to be used as needed.

%package compilers
Group:         Development/Libraries
Summary:       JSPC Compilers
Requires:      %{name} = %{version}-%{release}

%description compilers
%{summary}.

%package compiler-tomcat6
Group:         Development/Libraries
Summary:       JSPC Compiler for Tomcat6
Requires:      tomcat
Requires:      %{name}-compilers = %{version}-%{release}

%description compiler-tomcat6
%{summary}.

%package -n jspc-maven-plugin
Group:         Development/Libraries
Summary:       JSPC Maven Plugin
Requires:      %{name}-compiler-tomcat6 = %{version}-%{release}
Requires:      mvn(commons-lang:commons-lang)
Requires:      mvn(org.apache.maven.shared:file-management)

%description -n jspc-maven-plugin
%{summary}.

%package javadoc
Group:         Documentation
Summary:       Javadoc for %{name}

%description javadoc
This package contains javadoc for %{name}.

%prep
%setup -q -n %{name}

for d in LICENSE ; do
  iconv -f iso8859-1 -t utf-8 $d.txt > $d.txt.conv && mv -f $d.txt.conv $d.txt
  sed -i 's/\r//' $d.txt
done

# fix up gmaven removal in src
sed -i 's|import org.codehaus.groovy.maven.mojo.GroovyMojo|import org.apache.maven.plugin.AbstractMojo|' \
  jspc-maven-plugin/src/main/groovy/org/codehaus/mojo/jspc/CompilationMojoSupport.groovy
sed -i 's|extends GroovyMojo|extends AbstractMojo|' \
  jspc-maven-plugin/src/main/groovy/org/codehaus/mojo/jspc/CompilationMojoSupport.groovy

# plexus-maven-plugin superceded by plexus-component-metadata
sed -i 's|<artifactId>plexus-maven-plugin</artifactId>|<artifactId>plexus-component-metadata</artifactId>|' pom.xml

# no tomcat5
%pom_disable_module jspc-compiler-tomcat5 jspc-compilers/pom.xml

# switch jasper-jdt dep to ecj dep
%pom_remove_dep org.apache.tomcat:jasper-jdt jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_add_dep org.eclipse.jdt.core.compiler:ecj:3.1.1 jspc-compilers/jspc-compiler-tomcat6/pom.xml
sed -i 's|<artifactId>jasper</artifactId>|<artifactId>tomcat-jasper</artifactId>|' jspc-compilers/jspc-compiler-tomcat6/pom.xml
sed -i 's|<artifactId>jasper-el</artifactId>|<artifactId>tomcat-jasper-el</artifactId>|' jspc-compilers/jspc-compiler-tomcat6/pom.xml
sed -i 's|<artifactId>jasper-jdt</artifactId>|<artifactId>tomcat-jasper-jdt</artifactId>|' jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_remove_dep org.apache.tomcat:juli jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_remove_dep org.apache.tomcat:servlet-api jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_remove_dep org.apache.tomcat:jsp-api jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_remove_dep org.apache.tomcat:el-api jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_remove_dep org.apache.tomcat:annotations-api jspc-compilers/jspc-compiler-tomcat6/pom.xml

# drop plexus-maven-plugin and add plexus-component-metadata and appropriate config
%pom_remove_plugin org.codehaus.plexus:plexus-maven-plugin jspc-compilers/pom.xml
%pom_add_plugin org.codehaus.plexus:plexus-component-metadata jspc-compilers/pom.xml "
                <configuration>
                  <descriptors>
                    <descriptor>target/classes/META-INF/plexus/components.xml</descriptor>
                  </descriptors>
                </configuration>
                <executions>
                    <execution>
                        <id>create-component-descriptor</id>
                        <phase>generate-resources</phase>
                        <goals>
                            <goal>generate-metadata</goal>
                        </goals>
                    </execution>
                </executions>
"

# fix up source, target config in compiler plugin
%pom_remove_plugin org.apache.maven.plugins:maven-compiler-plugin pom.xml
%pom_add_plugin org.apache.maven.plugins:maven-compiler-plugin pom.xml "
                <configuration>
                    <source>1.7</source>
                    <target>1.7</target>
                </configuration>
"

# fix up source config in javadoc plugin
%pom_remove_plugin org.apache.maven.plugins:maven-javadoc-plugin pom.xml
%pom_add_plugin org.apache.maven.plugins:maven-javadoc-plugin pom.xml "
                <configuration>
                    <source>1.7</source>
                </configuration>
"

# remove wagon-webdav
%pom_xpath_remove "pom:build/pom:extensions"

# get rid of gmaven...
%pom_remove_dep org.codehaus.groovy.maven:gmaven-mojo pom.xml
%pom_remove_plugin org.codehaus.groovy.maven:gmaven-plugin pom.xml
%pom_add_dep 	org.apache.ant:ant jspc-compilers/jspc-compiler-tomcat6/pom.xml

#...replace with ant groovyc task
# have to patch due to some $ substitution problems
%patch0 -p2

%build

mvn-rpmbuild install javadoc:aggregate

# http://jira.codehaus.org/browse/GMAVEN-68
# gmaven-runtime 1.8 doesn't generate plugin descriptor
# files from javadoc, so we have to load in an existing
# one derived from mvn and g-r 1.6
mkdir -p META-INF/maven/
cp %{SOURCE1} META-INF/maven/plugin.xml
jar uf  %{name}-maven-plugin/target/%{name}-maven-plugin-2.0-alpha-3.jar META-INF/maven/plugin.xml

%install

mkdir -p %{buildroot}%{_mavenpomdir}
install -pm 644 pom.xml %{buildroot}%{_mavenpomdir}/JPP.%{name}-%{name}.pom
%add_maven_depmap JPP.%{name}-%{name}.pom

mkdir -p %{buildroot}%{_javadir}/%{name}

install -m 644 %{name}-compiler-api/target/%{name}-compiler-api-%{namedversion}.jar %{buildroot}%{_javadir}/%{name}/%{name}-compiler-api.jar
install -pm 644 %{name}-compiler-api/pom.xml %{buildroot}%{_mavenpomdir}/JPP.%{name}-%{name}-compiler-api.pom
%add_maven_depmap JPP.%{name}-%{name}-compiler-api.pom %{name}/%{name}-compiler-api.jar

install -pm 644 %{name}-compilers/pom.xml %{buildroot}%{_mavenpomdir}/JPP.%{name}-%{name}-compilers.pom
%add_maven_depmap JPP.%{name}-%{name}-compilers.pom

install -m 644 %{name}-compilers/%{name}-compiler-tomcat6/target/%{name}-compiler-tomcat6-%{namedversion}.jar \
  %{buildroot}%{_javadir}/%{name}/%{name}-compiler-tomcat6.jar
install -pm 644 %{name}-compilers/%{name}-compiler-tomcat6/pom.xml %{buildroot}%{_mavenpomdir}/JPP.%{name}-%{name}-compiler-tomcat6.pom
%add_maven_depmap JPP.%{name}-%{name}-compiler-tomcat6.pom %{name}/%{name}-compiler-tomcat6.jar

install -m 644 %{name}-maven-plugin/target/%{name}-maven-plugin-%{namedversion}.jar %{buildroot}%{_javadir}/%{name}/%{name}-maven-plugin.jar
install -pm 644 %{name}-maven-plugin/pom.xml %{buildroot}%{_mavenpomdir}/JPP.%{name}-%{name}-maven-plugin.pom
%add_maven_depmap JPP.%{name}-%{name}-maven-plugin.pom %{name}/%{name}-maven-plugin.jar

mkdir -p %{buildroot}%{_javadocdir}/%{name}
cp -pr target/site/apidocs/* %{buildroot}%{_javadocdir}/%{name}

%files
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}-compiler-api.jar
%{_mavenpomdir}/JPP.%{name}-%{name}.pom
%{_mavenpomdir}/JPP.%{name}-%{name}-compiler-api.pom
%{_mavendepmapfragdir}/%{name}
%doc LICENSE.txt

%files compilers
%dir %{_javadir}/%{name}
%{_mavenpomdir}/JPP.%{name}-%{name}-compilers.pom
%{_mavendepmapfragdir}/%{name}
%doc LICENSE.txt

%files compiler-tomcat6
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}-compiler-tomcat6.jar
%{_mavenpomdir}/JPP.%{name}-%{name}-compiler-tomcat6.pom
%{_mavendepmapfragdir}/%{name}
%doc LICENSE.txt

%files maven-plugin
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}-maven-plugin.jar
%{_mavenpomdir}/JPP.%{name}-%{name}-maven-plugin.pom
%{_mavendepmapfragdir}/%{name}
%doc LICENSE.txt

%files javadoc
%{_javadocdir}/%{name}
%doc LICENSE.txt

%changelog
* Tue Jun 11 2013 Peter MacKinnon <pmackinn@redhat.com> 2.0-0.5.alpha.3
- Removed tomcat-lib requires
- TODO: migrate to xmvn beyond F18

* Tue Jun 11 2013 Peter MacKinnon <pmackinn@redhat.com> 2.0-0.4.alpha.3
- Reinstated missing maven-install-plugin

* Thu May 30 2013 Peter MacKinnon <pmackinn@redhat.com> 2.0-0.3.alpha.3
- Updates from peer review

* Tue May 07 2013 Peter MacKinnon <pmackinn@redhat.com> 2.0-0.2.alpha.3
- Re-org sub-package dependencies

* Fri Apr 05 2013 Peter MacKinnon <pmackinn@redhat.com> 2.0-0.1.alpha.3
- Initial rpm
