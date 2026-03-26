"""
CSS styling configuration and application module for the CarPool rental system.

This module provides the StyleConfig class for parsing TOML configuration files
and converting them into CSS stylesheets for Streamlit UI elements.
"""

import streamlit as st
import toml
import json
from os.path import join, dirname

#update debugging to st.session_state['variables']['debug']['enabled'] 

class StyleConfig():
    """
    StyleConfig class combines style configuration TOML files into CSS stylesheets.
    
    Parses TOML configuration files and converts them into CSS rules that can be
    applied to Streamlit elements. Supports custom rules for colors, borders, and columns.
    """

    def __init__(self, styleConfigPath: str, debugging=False) -> None:
        """
        Initialize the StyleConfig with a TOML configuration file.
        
        Args:
            styleConfigPath (str): Path to the TOML configuration file
            debugging (bool): Enable debugging output (default False)
        """
        #====================================================================================================================
        #----   Initialize Base Path and Configuration   -------------------------------------------------------------------

        self.base_url = join(dirname(__file__), '..')

        self.debugging = debugging

        self.style_config = toml.load( open( join(self.base_url, styleConfigPath ), 'r') ) 

        self.extraFonts = {}
        for font in self.style_config['config-header']['font']:
            self.extraFonts['@font-face'] = {
                'font-family' : font
                ,'src' : f'url("../css/{font}.ttf") format("truetype")'
            }

        #====================================================================================================================
        #----   Load CSS Templates from Files   --------------------------------------------------------------------------

        self.templates = {}
        self.elements = {}
        self.customRules = {}

        self.templates['id_button']     = self.__css_parser(open( join( self.base_url, 'CSS/id_button.css'), 'r').read())
        self.templates['id_expander']   = self.__css_parser(open( join( self.base_url, 'CSS/id_expander.css'), 'r').read())
        self.templates['id_table']      = self.__css_parser(open( join( self.base_url, 'CSS/id_table.css'), 'r').read())
        self.templates['id_input']      = self.__css_parser(open( join( self.base_url, 'CSS/id_input.css'), 'r').read())
        self.templates['id_dropdown']   = self.__css_parser(open( join( self.base_url, 'CSS/id_dropdown.css'), 'r').read())

        self.templates['class_button']  = self.__css_parser(open( join( self.base_url, 'CSS/class_button.css'), 'r').read())
        self.templates['class_expander']= self.__css_parser(open( join( self.base_url, 'CSS/class_expander.css'), 'r').read())
        self.templates['class_table']   = self.__css_parser(open( join( self.base_url, 'CSS/class_table.css'), 'r').read())
        self.templates['class_input']   = self.__css_parser(open( join( self.base_url, 'CSS/class_input.css'), 'r').read())
        self.templates['class_dropdown']= self.__css_parser(open( join( self.base_url, 'CSS/class_dropdown.css'), 'r').read())

        self.elements['button'] = toml.load( open( join( self.base_url, 'CSS/element_button.toml' ) ) )
        self.elements['table'] = toml.load( open( join( self.base_url, 'CSS/element_table.toml' ) ) )
        self.elements['expander'] = toml.load( open( join( self.base_url, 'CSS/element_expander.toml' ) ) )
        self.elements['input'] = toml.load( open( join( self.base_url, 'CSS/element_input.toml' ) ) )
        self.elements['dropdown'] = toml.load( open( join( self.base_url, 'CSS/element_dropdown.toml' ) ) )

        #====================================================================================================================
        #----   Define Custom CSS Rule Handlers   -------------------------------------------------------------------------

        def CustomRule_ColumnValue(elementStyleSheet, rule_group, rule_type, rule_name, CSSRuleValue):
            """Apply different CSS values to each column."""
            for i in range(len(CSSRuleValue)):
                column_rule = rule_group.replace('||Column||', str(i+2))
                if CSSRuleValue[i] == '':
                    continue
                if column_rule in elementStyleSheet.keys():
                    elementStyleSheet[column_rule][rule_name] = CSSRuleValue[i]
                else:
                    elementStyleSheet[column_rule] = { rule_name : CSSRuleValue[i] }
            
            return elementStyleSheet

        def CustomRule_BorderSize(elementStyleSheet, rule_group, rule_type, rule_name, CSSRuleValue):
            """Handle border size configurations for single/multi-sided borders."""
            borderSize = CSSRuleValue
            borderSide = ['border-top', 'border-left', 'border-bottom', 'border-right']

            if 'border' in elementStyleSheet[rule_group].keys():
                borderStyle = 'Single'
            elif 'border-top' in elementStyleSheet[rule_group].keys():
                borderStyle = 'Multi'
            else:
                borderStyle = 'None'

            if type(borderSize) == list and borderStyle == 'Single':
                col = elementStyleSheet[rule_group]['border'].split('1px')[-1].strip()
                del elementStyleSheet[rule_group]['border']
                for i in range(4):
                    if borderSide[i] == '':
                        elementStyleSheet[rule_group][borderSide[i]] = f'solid 1px {col}'
                    else:
                        elementStyleSheet[rule_group][borderSide[i]] = f'solid {borderSize[i]} {col}'
                    
            elif type(borderSize) == list and borderStyle == 'Multi':
                for i in range(4):
                    if borderSide[i] == '':
                        continue
                    else:
                        elementStyleSheet[rule_group][borderSide[i]].replace('1px', borderSize[i])
                    

            elif type(borderSize) == list and borderStyle == 'None':
                for i in range(4):
                    if borderSide[i] == '':
                        elementStyleSheet[rule_group][borderSide[i]] = f'solid 1px'
                    else:
                        elementStyleSheet[rule_group][borderSide[i]] = f'solid {borderSize[i]}'

            elif type(borderSize) == str and borderStyle == 'Single':
                elementStyleSheet[rule_group]['border'].replace('1px', borderSize)

            elif type(borderSize) == str and borderStyle == 'Multi':
                for i in range(4):
                    elementStyleSheet[rule_group][borderSide[i]].replace('1px', borderSize)

            elif type(borderSize) == str and borderStyle == 'None':
                elementStyleSheet[rule_group]['border'] = f'solid {borderSize}'

            return elementStyleSheet
        
        def CustomRule_BorderColour(elementStyleSheet, rule_group, rule_type, rule_name, CSSRuleValue):
            """Handle border color configurations for single/multi-sided borders."""
            borderColour = CSSRuleValue
            borderSide = ['border-top', 'border-left', 'border-bottom', 'border-right']

            if 'border' in elementStyleSheet[rule_group].keys():
                borderStyle = 'Single'
            elif 'border-top' in elementStyleSheet[rule_group].keys():
                borderStyle = 'Multi'
            else:
                borderStyle = 'None'

            if type(borderColour[0]) == list and borderStyle == 'Single':
                #delete Rule and turn into multi
                size = elementStyleSheet[rule_group]['border'].split('solid')[-1].strip()
                del elementStyleSheet[rule_group]['border']
                for i in range(4):
                    if len(borderColour[i]) == 0:
                        elementStyleSheet[rule_group][borderSide[i]] = f'solid {size}'
                    else:
                        col = self.__list_to_col(borderColour[i])
                        elementStyleSheet[rule_group][borderSide[i]] = f'solid {size} {col}'

            elif type(borderColour[0]) == list and borderStyle == 'Multi':
                for i in range(4):
                    if len(borderColour[i]) == 0:
                        continue
                    else:
                        col = self.__list_to_col(borderColour[i])
                        elementStyleSheet[rule_group][borderSide[i]] = elementStyleSheet[rule_group][borderSide[i]] + f' {col}'

            elif type(borderColour[0]) == list and borderStyle == 'None':
                for i in range(4):
                    if len(borderColour[i]) == 0:
                       elementStyleSheet[rule_group][borderSide[i]] = 'solid 1px'
                    else:
                        col = self.__list_to_col(borderColour[i])
                        elementStyleSheet[rule_group][borderSide[i]] = f'solid 1px {col}'

            elif type(borderColour) == list and borderStyle == 'Single':
                col = self.__list_to_col(borderColour)
                elementStyleSheet[rule_group]['border'] = elementStyleSheet[rule_group]['border'] + f' {col}'

            elif type(borderColour) == list and borderStyle == 'Multi':
                col = self.__list_to_col(borderColour)
                for i in range(4):
                    elementStyleSheet[rule_group][borderSide[i]] = elementStyleSheet[rule_group][borderSide[i]] + f' {col}'

            elif type(borderColour) == list and borderStyle == 'None':
                col = self.__list_to_col(borderColour)
                elementStyleSheet[rule_group]['border'] = f'solid 1px {col}'

            return elementStyleSheet


        self.customRules['CustomRule_column-value'] = CustomRule_ColumnValue
        self.customRules['CustomRule_border-size'] = CustomRule_BorderSize
        self.customRules['CustomRule_border-colour'] = CustomRule_BorderColour

    def __css_parser(self, txt: str) -> dict:
        """
        Convert CSS element stylesheet text into a dictionary structure.
        
        Args:
            txt (str): CSS text to parse
        
        Returns:
            dict: Dictionary representation of CSS rules and properties
        """
        #====================================================================================================================
        #----   Parse CSS Text into Dictionary Structure   ---------------------------------------------------------------

        elementSheet = {}
        txt = txt.replace('\n','')
        list_of_rules = txt.split('}')
        for rule in list_of_rules:
            if rule.strip() == '':
                continue
            ruleText, paraString = rule.split('{')
            elementSheet[ruleText.strip()] = {}
            for para in paraString.split(';'):
                if para.strip() == '':
                    continue
                paraName, paraValue = para.split(':')
                elementSheet[ruleText.strip()][paraName.strip()] = paraValue.strip()
        
        return elementSheet
    
    def __css_wrtiter(self, cssDict):
        """
        Convert dictionary CSS structure back into CSS text format.
        
        Args:
            cssDict (dict): Dictionary representation of CSS rules
        
        Returns:
            str: Formatted CSS text
        """
        #====================================================================================================================
        #----   Format Dictionary as CSS Text   --------------------------------------------------------------------------

        rules = cssDict.keys()
        txt = ''
        for rule in rules:
            ruleString = rule + ' {\n'
            for paraName in cssDict[rule].keys():
                ruleString += f'   {paraName}: {cssDict[rule][paraName]};\n'
            ruleString += '}\n'
            txt += ruleString
        
        return txt[:-1]
    
    def __list_to_col(self, lst: list) -> str:
        """
        Convert a list [R, G, B] or [R, G, B, A] into RGBA color format.
        
        Args:
            lst (list): RGB or RGBA color values
        
        Returns:
            str: RGBA format color string
        """
        #====================================================================================================================
        #----   Convert List to RGBA Color String   -----------------------------------------------------------------------

        if len(lst) == 3:
            lst.append(1)
        return 'rgba' + str(tuple(lst))

    def __parser_main(self, elementStyleSheet, config, CSSRule, rule_group, rule_type, rule_name):
        """
        Main parser for applying CSS rules to element stylesheets.
        
        Args:
            elementStyleSheet (dict): The CSS stylesheet being built
            config (dict): Configuration values
            CSSRule (str): The CSS rule name
            rule_group (str): The CSS selector/rule group
            rule_type (str): Type of rule (color, value, or custom rule name)
            rule_name (str): CSS property name
        
        Returns:
            dict: Updated stylesheet
        """
        #====================================================================================================================
        #----   Apply CSS Rule to Stylesheet   ---------------------------------------------------------------------------

        CSSRuleValue = config[CSSRule]
        

        if rule_group not in elementStyleSheet.keys():
                elementStyleSheet[rule_group] = {}

        if rule_type == 'colour':
            elementStyleSheet[rule_group][rule_name] = self.__list_to_col( CSSRuleValue )
            
        elif rule_type == 'value':
            elementStyleSheet[rule_group][rule_name] = CSSRuleValue

        elif rule_type[0] == '"' and rule_type[-1] == '"':
            elementStyleSheet[rule_group][rule_name] = rule_type[1:-1]
        
        else:
            KArgs = ( elementStyleSheet, rule_group, rule_type, rule_name, CSSRuleValue )
            elementStyleSheet = self.customRules[rule_type]( *KArgs )
        
        return elementStyleSheet


    def __write_template(self, configName, config):
        """
        Generate CSS stylesheet from configuration template.
        
        Args:
            configName (str): Name of the configuration
            config (dict): Configuration values
        
        Returns:
            dict: CSS stylesheet dictionary
        """
        #====================================================================================================================
        #----   Load Base Templates and Element Configuration   ----------------------------------------------------------

        elementType = config['css_element_type']
        elementScope = config['scope']      
        elementMapping = self.elements[elementType]  
        elementStyleSheet = {}

        for style in self.templates[f'{elementScope}_{elementType}'].keys():
            specific_style = style.replace('__ConfigName__', configName)
            elementStyleSheet[specific_style] = self.templates[f'{elementScope}_{elementType}'][style].copy()

        base_rules = elementMapping[elementScope].copy()
        for rule in base_rules.keys():
            base_rules[rule] = base_rules[rule].replace('||ConfigName||', configName)

        rulesAdded = 0
        for CSSRule in config.keys():
            if CSSRule in ['css_element_type', 'scope']:
                continue

            rule_group_name = elementMapping[CSSRule]['rule_group']

            if type(rule_group_name) == list:
                for i in range(len(rule_group_name)):
                    rule_name =  elementMapping[CSSRule]['rule_name'][i]
                    rule_type =  elementMapping[CSSRule]['rule_type'][i]
                    rule_group = base_rules[rule_group_name[i]]

                    elementStyleSheet = self.__parser_main( 
                                            elementStyleSheet=elementStyleSheet
                                        ,config = config
                                        ,CSSRule=CSSRule
                                        ,rule_group=rule_group
                                        ,rule_type=rule_type
                                        ,rule_name=rule_name
                                    )
            else:
                rule_name =  elementMapping[CSSRule]['rule_name']
                rule_type =  elementMapping[CSSRule]['rule_type']
                rule_group = base_rules[rule_group_name]

                elementStyleSheet = self.__parser_main( 
                                        elementStyleSheet=elementStyleSheet
                                    ,config = config
                                    ,CSSRule=CSSRule
                                    ,rule_group=rule_group
                                    ,rule_type=rule_type
                                    ,rule_name=rule_name
                                )
            
            rulesAdded += 1
        
        if rulesAdded == 0:
            elementStyleSheet = ''

        return elementStyleSheet



    def __BUILD(self) -> str:
        '''builds a style sheet from the self.StyleSheetDict'''
        styleSheet = '<style>\n'

        #--style string: Add fonts 
        fontStyleString = self.__css_wrtiter( cssDict=self.extraFonts )
        styleSheet += f'{ fontStyleString }\n'

        for elementName in self.style_config.keys():
            if elementName == 'config-header':
                continue

            elementConfig = self.style_config[ elementName ]
            elementStyleSheet = self.__write_template( configName=elementName, config=elementConfig )

            #--style string: Add elements
            elementStyleString = self.__css_wrtiter( cssDict=elementStyleSheet )
            styleSheet += f'{ elementStyleString }\n'

        styleSheet += '</style>'
        return styleSheet

    def AddStyleSheet(self, cont=st):
        if self.debugging:
            st.write("Applying Style Sheet")
        styleSheet = self.__BUILD()
        if self.debugging:
            with open('EXPORT_styleSheet.css', 'w') as f:
                f.write(styleSheet)
                
        cont.html( styleSheet )

    def LabelElement(self, configName, container=st):
        container.markdown(f'<span id="{ configName }"></span>', unsafe_allow_html=True)