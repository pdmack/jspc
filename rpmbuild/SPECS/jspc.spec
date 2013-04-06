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

BuildRequires: java-devel
BuildRequires: jpackage-utils
BuildRequires: maven
BuildRequires: gmaven
BuildRequires: ant

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

%package compiler-api
Group:         Development/Libraries
Summary:       JSPC Compiler API
Requires:      jpackage-utils
Requires:      %{name} = %{version}-%{release}

%description compiler-api
%{summary}.

%package compilers
Group:         Development/Libraries
Summary:       JSPC Compiler for Tomcat6
Requires:      jpackage-utils
Requires:      %{name} = %{version}-%{release}

%description compilers
%{summary}.

%package -n jspc-maven-plugin
Group:         Development/Libraries
Summary:       JSPC Maven Plugin
Requires:      jpackage-utils
Requires:      %{name} = %{version}-%{release}
Requires:      %{name}-compiler-api = %{version}-%{release}
Requires:      %{name}-compilers = %{version}-%{release}

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

# fix up tomcat6 pom
%pom_add_dep org.codehaus.gmaven.runtime:gmaven-runtime:1.8 jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_xpath_inject "pom:dependencies/pom:dependency[pom:artifactId[./text()='jasper']]" "
            <exclusions>
              <exclusion>
                <groupId>org.eclipse.jdt.core.compiler</groupId>
                <artifactId>ecj</artifactId>
              </exclusion>
            </exclusions>
" jspc-compilers/jspc-compiler-tomcat6/pom.xml
%pom_xpath_inject "pom:dependencies/pom:dependency[pom:artifactId[./text()='jasper-jdt']]" "
            <!-- tomcat6-lib package not generating JPP POMS for jasper-jdt -->
            <scope>system</scope>
            <systemPath>/usr/share/java/tomcat6/jasper-jdt.jar</systemPath>
" jspc-compilers/jspc-compiler-tomcat6/pom.xml

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
  install javadoc:aggregate

%install

mkdir -p %{buildroot}%{_mavenpomdir}
install -pm 644 pom.xml %{buildroot}%{_mavenpomdir}/JPP.%{name}-%{name}.pom
%add_maven_depmap JPP.%{name}-%{name}.pom

mkdir -p %{buildroot}%{_javadir}/%{name}

%files
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/%{name}-api.jar
%{_mavenpomdir}/JPP.%{name}-%{name}.pom
%{_mavenpomdir}/JPP.%{name}-%{name}-api.pom
%{_mavendepmapfragdir}/%{name}
%doc LICENSE.txt

%files javadoc
%{_javadocdir}/%{name}
%doc LICENSE.txt

%changelog
* Fri Apr 05 2013 Peter MacKinnon <pmackinn@redhat.com> 2.0-0.1.alpha.3
- Initial rpm
