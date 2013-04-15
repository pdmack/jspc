%global namedreltag  -alpha-3
%global namedversion %{version}%{?namedreltag}
%global dotreltag    %(echo %{namedreltag} | tr - .)

Name:          jspc
Version:       2.0
Release:       0.1%{dotreltag}%{?dist}
Summary:       Compile JSPs under Maven
Group:         Development/Libraries
License:       ASL 2.0
Url:           http://mojo.codehaus.org/jspc/
# svn export https://svn.codehaus.org/mojo/tags/jspc-2.0-alpha-3 jspc
# tar czf jspc-2.0-alpha-3-src-svn.tar.gz jspc
Source0:       %{name}-%{namedversion}-src-svn.tar.gz
Source1:       jspc-mp-plugin.xml

BuildRequires: java-devel
BuildRequires: jpackage-utils
BuildRequires: maven

BuildRequires: apache-resource-bundles
BuildRequires: ant
BuildRequires: fusesource-pom
BuildRequires: gmaven
BuildRequires: plexus-container-default
BuildRequires: tomcat

BuildRequires: maven-compiler-plugin
BuildRequires: maven-enforcer-plugin
BuildRequires: maven-install-plugin
BuildRequires: maven-invoker-plugin
BuildRequires: maven-javadoc-plugin
BuildRequires: maven-plugin-cobertura
BuildRequires: maven-plugin-plugin
BuildRequires: maven-release-plugin
BuildRequires: maven-remote-resources-plugin
BuildRequires: maven-surefire-plugin

Requires:      java
Requires:      jpackage-utils
BuildArch:     noarch

%description
The Codehaus is a collaborative environment for building open source projects
with a strong emphasis on modern languages, focussed on quality components that
meet real world needs.

Provides support to precompile your JSPs and have them included into your WAR file.
Version 2 of the JSP compilation support includes a pluggable JSP compiler
implementation, which currently allows different versions of the Tomcat Jasper
compiler to be used as needed.

%package compiler-tomcat6
Group:         Development/Libraries
Summary:       JSPC Compiler for Tomcat6
Requires:      jpackage-utils
Requires:      tomcat
Requires:      %{name} = %{version}-%{release}

%description compiler-tomcat6
%{summary}.

%package -n jspc-maven-plugin
Group:         Development/Libraries
Summary:       JSPC Maven Plugin
Requires:      jpackage-utils
Requires:      %{name} = %{version}-%{release}
Requires:      %{name}-compiler-tomcat6 = %{version}-%{release}

%description -n jspc-maven-plugin
%{summary}.

%package javadoc
Group:         Documentation
Summary:       Javadoc for %{name}
Requires:      jpackage-utils

%description javadoc
This package contains javadoc for %{name}.

%prep
%setup -q -n %{name}

for d in LICENSE ; do
  iconv -f iso8859-1 -t utf-8 $d.txt > $d.txt.conv && mv -f $d.txt.conv $d.txt
  sed -i 's/\r//' $d.txt
done

# fix up gmaven namespace change in src
sed -i 's|import org.codehaus.groovy.maven|import org.codehaus.gmaven|' \
  jspc-maven-plugin/src/main/groovy/org/codehaus/mojo/jspc/CompilationMojoSupport.groovy

# fix up gmaven namespace change in poms
sed -i 's|<groupId>org.codehaus.groovy.maven</groupId>|<groupId>org.codehaus.gmaven</groupId>|' pom.xml
sed -i 's|<groupId>org.codehaus.groovy.maven</groupId>|<groupId>org.codehaus.gmaven</groupId>|' jspc-maven-plugin/pom.xml

# plexus-maven-plugin superceded by plexus-component-metadata
sed -i 's|<artifactId>plexus-maven-plugin</artifactId>|<artifactId>plexus-component-metadata</artifactId>|' pom.xml

# no tomcat5
%pom_disable_module jspc-compiler-tomcat5 jspc-compilers/pom.xml

# dump wagon-webdav
%pom_xpath_remove "pom:build/pom:extensions" pom.xml

# fix up tomcat6 pom to point to TC7 refs
sed -i 's|Tomcat 6|Tomcat 7|' jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_add_dep org.codehaus.gmaven.runtime:gmaven-runtime-1.8:1.4 jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_xpath_inject "pom:dependencies/pom:dependency[pom:artifactId[./text()='jasper']]" "
            <exclusions>
              <exclusion>
                <groupId>org.eclipse.jdt.core.compiler</groupId>
                <artifactId>ecj</artifactId>
              </exclusion>
            </exclusions>
" jspc-compilers/jspc-compiler-tomcat6/pom.xml
# tomcat-lib package not generating JPP POMS for jasper-jdt
%pom_xpath_inject "pom:dependencies/pom:dependency[pom:artifactId[./text()='jasper-jdt']]" "
            <scope>system</scope>
            <systemPath>\${tomcat.jasperjdt.local}</systemPath>
" jspc-compilers/jspc-compiler-tomcat6/pom.xml
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

# be quiet about missing help mojo descriptors
%pom_xpath_inject "pom:build/pom:plugins/pom:plugin[pom:artifactId[./text()='maven-plugin-plugin']]" "
                <configuration>
                  <skipErrorNoDescriptorsFound>true</skipErrorNoDescriptorsFound>
                </configuration>
" jspc-maven-plugin/pom.xml

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

%build

mvn-rpmbuild \
  -Dgmaven.runtime=1.8 \
  -Dtomcat.jasperjdt.local=/usr/share/java/tomcat/jasper-jdt.jar \
  install javadoc:aggregate

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
* Fri Apr 05 2013 Peter MacKinnon <pmackinn@redhat.com> 2.0-0.1.alpha.3
- Initial rpm
