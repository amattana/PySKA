f=open('aavs1_ship.txt','r')
a=f.readlines()
f.close()

out=open('aavs1.xml','w')
out.write("<?xml version=\"1.0\" encoding=\"ISO-8859-15\"?>\n") 
out.write("\n<project name='SKA-LAB'> <!-- First entry -->\n")

#for line in a:
#  print line.split()
#exit()
for line in a:
  c=line.split()

  out.write("	<iTPM id='"+c[0]+"'>\n")
  out.write("        <subrack_position>"+str(((int(c[0])-1)%4))+"</subrack_position> \n")
  out.write("		<serial>"+c[1]+"</serial>\n")
  out.write("		<ipaddr>"+c[2]+"</ipaddr>\n")
  out.write("		<macaddr>"+c[3]+"</macaddr>\n")
  out.write("		<udpport>10000</udpport>\n")
  out.write("        <udptimeout>1</udptimeout>\n")
  out.write("		<preadu_l>"+c[4]+"</preadu_l>\n")
  out.write("		<preadu_r>"+c[5]+"</preadu_r>\n")
  out.write("	</iTPM>\n")
  

out.write("</project>")
